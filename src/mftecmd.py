import os
import shutil
import subprocess
import time
from uuid import uuid4

from celery import signals
from celery.utils.log import get_task_logger

from openrelik_worker_common.file_utils import create_output_file
from openrelik_worker_common.task_utils import create_task_result, get_input_files

from pathvalidate import sanitize_filename

from .app import celery

# Task name used to register and route the task to the correct queue.
TASK_NAME = "openrelik-worker-mftecmd.tasks.mftecmd"

# Task metadata for registration in the core system.
TASK_METADATA = {
    "display_name": "Eric Zimmerman's MFTECmd ",
    "description": "Runs Eric Zimmerman's MFTECmd  application on MFT files",
}

COMPATIBLE_INPUTS = {
    "data_types": [],
    "mime_types": ["application/octet-stream", "text/plain"],
    "filenames": [
        "$Boot",
        "$I30","INDX",
        "$UsnJrnl%3A$J","$J","UsnJrnl-J",
        "$MFT",
        "$Secure_$SDS","$Secure%3A$SDS",
        "$LogFile",
        ".openrelik-hostname"
        ],
}

@celery.task(bind=True, name=TASK_NAME, metadata=TASK_METADATA)
def mftecmd(
    self,
    pipe_result=None,
    input_files=[],
    output_path=None,
    workflow_id=None,
    task_config={},
) -> str:
    output_files = []
    input_files = get_input_files(pipe_result, input_files or [], filter=COMPATIBLE_INPUTS)
    if not input_files:
        return create_task_result(
            output_files=output_files,
            workflow_id=workflow_id,
            command="",
        )

    # .openrelik-hostname support
    prefix = ""
    if (hostname_item := next((f for f in input_files if f.get('display_name') == ".openrelik-hostname"), None)):
        with open(hostname_item.get('path'),"r", encoding="utf-8") as f:
            raw_hostname = f.read().strip()
        prefix = f"{sanitize_filename(raw_hostname)}_"

    # Create temporary directory and hard link files for processing
    temp_dir = os.path.join(output_path, uuid4().hex)
    os.mkdir(temp_dir)
    # don't run on the .openrelik-hostname file
    for file in (f for f in input_files if f.get('display_name') != ".openrelik-hostname"):
        filename = os.path.basename(file.get("path"))
        os.link(file.get("path"), f"{temp_dir}/{filename}")

        output_file = create_output_file(
            output_path,
            display_name=f"{prefix}{file.get('display_name')}_MFTECmd_output.csv",
            data_type="openrelik:mftecmd:mftecmd",
        )

        command = [
            "dotnet",
            "/mftecmd/MFTECmd.dll",
            "-f",
            file.get("path"),
            "--csv",
            output_path,
            "--csvf",
            output_file.path,
        ]

        # add mft enrichment if this is a journal file and an mft file exists
        if file.get('display_name') in ["$UsnJrnl%3A$J","$J","UsnJrnl-J"]:
            if (mft_item := next((f for f in input_files if f.get('display_name') == "$MFT"), None)):
                command.append('-m')
                command.append(mft_item.get("path"))

        INTERVAL_SECONDS = 2
        process = subprocess.Popen(command)
        while process.poll() is None:
            self.send_event("task-progress", data=None)
            time.sleep(INTERVAL_SECONDS)
        
        output_files.append(output_file.to_dict())

    # Remove temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    return create_task_result(
        output_files=output_files,
        workflow_id=workflow_id,
        command=" ".join(command),
    )
