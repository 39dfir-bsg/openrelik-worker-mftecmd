# Openrelik worker mftecmd
## Description
This worker runs eric zimmerman's mftecmd application against mft files.

When extracting from a zip archive, I'd reccomend the following glob.

```
*$Boot,*$I30,*INDX,*$UsnJrnl%3A$J,*$J,*UsnJrnl-J,*$MFT,*$Secure_$SDS,*$Secure%3A$SDS,*$LogFile
```

If you provide a journal ($J) artifact and an MFT ($MFT) artifact, it will automatically use the MFT artifact to enrich the journal output.

Therefore, this worker does not support running output from multiple hosts at once.

## Deploy
Add the below configuration to the OpenRelik docker-compose.yml file after updating the `īmage` section to point to the workflow published container.

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
