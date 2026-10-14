"""One command: dev server, worker process, client process, then clean shutdown."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from temporalio.testing import WorkflowEnvironment

HERE = Path(__file__).parent
PORT = int(os.environ.get("TEMPORAL_PORT", "7233"))


async def main() -> int:
    async with await WorkflowEnvironment.start_local(port=PORT, ui=False) as env:
        address = f"127.0.0.1:{PORT}"
        child_env = {**os.environ, "TEMPORAL_ADDRESS": address}
        worker = subprocess.Popen([sys.executable, "worker.py"], cwd=HERE, env=child_env, stdout=subprocess.PIPE, text=True)
        try:
            assert worker.stdout is not None
            for line in worker.stdout:
                print(f"[worker] {line.rstrip()}", flush=True)
                if "WORKER_READY" in line:
                    break
            client = await asyncio.create_subprocess_exec(sys.executable, "client.py", cwd=HERE, env=child_env)
            return await client.wait()
        finally:
            worker.terminate()
            worker.wait(timeout=30)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
