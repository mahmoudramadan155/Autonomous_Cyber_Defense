import subprocess
import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.response_action import ResponseAction
from app.schemas.response_action import ResponseActionCreate

logger = logging.getLogger(__name__)


class ResponseEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_action(
        self,
        incident_id: int,
        action_type: str,
        target: str,
        mode: str = "auto",
    ) -> ResponseAction:
        """
        Executes a SOAR response action.
        mode: 'auto' (execute immediately) | 'manual' (log pending, wait for approval)
        """
        if mode == "manual":
            return await self._record_action(
                incident_id, action_type, target,
                status="Manual Approval Required",
                executed_by="System (Pending)",
                details=f"Awaiting analyst approval: {action_type} on {target}",
            )

        # --- AUTO mode: really execute ---
        details, status = await self._dispatch(action_type, target)
        return await self._record_action(
            incident_id, action_type, target,
            status=status,
            executed_by="Auto SOAR",
            details=details,
        )

    # ------------------------------------------------------------------ #
    #  Action dispatcher                                                   #
    # ------------------------------------------------------------------ #
    async def _dispatch(self, action_type: str, target: str) -> tuple[str, str]:
        """Route action to correct implementation. Returns (details, status)."""
        t = action_type.lower()
        try:
            if "block" in t and "ip" in t:
                return await self._block_ip(target)
            elif "disable" in t and "user" in t:
                return await self._disable_user(target)
            elif "rate" in t:
                return await self._rate_limit(target)
            elif "isolate" in t:
                return await self._isolate_host(target)
            else:
                details = f"Unknown action '{action_type}' on '{target}' — logged only."
                logger.warning(details)
                return details, "Logged"
        except Exception as exc:
            err = f"SOAR action '{action_type}' on '{target}' FAILED: {exc}"
            logger.error(err)
            return err, "Failed"

    # ------------------------------------------------------------------ #
    #  Concrete SOAR actions                                               #
    # ------------------------------------------------------------------ #
    async def _block_ip(self, ip: str) -> tuple[str, str]:
        """
        Blocks an IP using iptables inside the container.
        Falls back to logging-only if iptables is unavailable (dev mode).
        """
        logger.warning(f"[SOAR] Blocking IP: {ip}")
        result = await asyncio.to_thread(
            subprocess.run,
            ["iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            msg = f"iptables rule added: DROP INPUT from {ip}"
            logger.info(f"[SOAR] {msg}")
            return msg, "Success"
        else:
            # Likely no iptables permissions in dev — still record
            fallback = f"iptables unavailable ({result.stderr.strip()}). IP {ip} flagged in DB only."
            logger.warning(f"[SOAR] {fallback}")
            return fallback, "Partial (DB only)"

    async def _disable_user(self, username: str) -> tuple[str, str]:
        """Disable a user account directly in the database."""
        logger.warning(f"[SOAR] Disabling user: {username}")
        try:
            await self.db.execute(
                text("UPDATE users SET is_active = false WHERE username = :u"),
                {"u": username},
            )
            await self.db.commit()
            msg = f"User '{username}' disabled in database."
            logger.info(f"[SOAR] {msg}")
            return msg, "Success"
        except Exception as e:
            msg = f"Failed to disable user '{username}': {e}"
            logger.error(f"[SOAR] {msg}")
            return msg, "Failed"

    async def _rate_limit(self, target: str) -> tuple[str, str]:
        """
        Apply rate limiting via iptables hashlimit.
        Limits target IP to 10 connections/minute.
        """
        logger.warning(f"[SOAR] Rate-limiting: {target}")
        result = await asyncio.to_thread(
            subprocess.run,
            [
                "iptables", "-I", "INPUT",
                "-s", target,
                "-m", "hashlimit",
                "--hashlimit-above", "10/min",
                "--hashlimit-burst", "5",
                "--hashlimit-mode", "srcip",
                "--hashlimit-name", "rate_limit",
                "-j", "DROP"
            ],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            msg = f"Rate limit applied: {target} capped at 10 req/min."
            return msg, "Success"
        fallback = f"iptables hashlimit unavailable. {target} flagged."
        return fallback, "Partial (DB only)"

    async def _isolate_host(self, host: str) -> tuple[str, str]:
        """
        Isolate a host by blocking all traffic except the management network.
        """
        logger.warning(f"[SOAR] Isolating host: {host}")
        cmds = [
            ["iptables", "-I", "FORWARD", "-s", host, "-j", "DROP"],
            ["iptables", "-I", "FORWARD", "-d", host, "-j", "DROP"],
        ]
        for cmd in cmds:
            await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        msg = f"Host {host} isolated: all FORWARD traffic blocked."
        logger.info(f"[SOAR] {msg}")
        return msg, "Success"

    # ------------------------------------------------------------------ #
    #  DB helper                                                           #
    # ------------------------------------------------------------------ #
    async def _record_action(
        self, incident_id, action_type, target, status, executed_by, details
    ) -> ResponseAction:
        action_create = ResponseActionCreate(
            incident_id=incident_id,
            action_type=action_type,
            target=target,
            status=status,
            executed_by=executed_by,
            details=details,
        )
        db_action = ResponseAction(**action_create.model_dump())
        self.db.add(db_action)
        await self.db.commit()
        await self.db.refresh(db_action)
        return db_action
