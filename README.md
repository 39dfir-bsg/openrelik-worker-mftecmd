# Openrelik worker mftecmd
## Description
This worker runs eric zimmerman's mftecmd application against mft files.

When extracting from a zip archive, I'd reccomend the following glob.

```
*$Boot,*$I30,*INDX,*$UsnJrnl%3A$J,*$J,*UsnJrnl-J,*$MFT,*$Secure_$SDS,*$Secure%3A$SDS,*$LogFile
```

If you provide a journal ($J) artifact and an MFT ($MFT) artifact, it will automatically use the MFT artifact to enrich the journal output.

Therefore, this worker does not support running output from multiple hosts at once.

Supports `.openrelik-hostname` files.

Supply a `.openrelik-hostname` file to this worker and it will prefix any output with the included hostname. If you're running an extract from an archive task before this, place your `.openrelik-hostname` file in an archive (eg. `openrelik-config.zip`) and add globs for it (`*.openrelik-hostname`) to your extract from archive task.

## Deploy
Update your `config.env` file to set `OPENRELIK_WORKER_MFTECMD_VERSION` to the tagged release version you want to use.

Add the below configuration to the OpenRelik docker-compose.yml file, you may need to update the `image:` value to point to the container in a  registry.

```
openrelik-worker-mftecmd:
    container_name: openrelik-worker-mftecmd
    image: openrelik-worker-mftecmd:${OPENRELIK_WORKER_MFTECMD_VERSION}
    restart: always
    environment:
      - REDIS_URL=redis://openrelik-redis:6379
    volumes:
      - ./data:/usr/share/openrelik/data
    command: "celery --app=src.app worker --task-events --concurrency=4 --loglevel=INFO -Q openrelik-worker-mftecmd"
    
    # ports:
      # - 5678:5678 # For debugging purposes.
```
