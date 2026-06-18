# Code Shadowing Report

## Structural Analysis of Current Flaw
Code shadowing occurred because Hugging Face Persistent Storage was configured natively against `/home/user/app`—the exact working directory hosting the live repository. Since Docker isolates environments via layered filesystems, the Hugging Face runtime executed the volume attachment *after* the Docker pull. This completely decoupled the application logic from the GitHub remote branch by trapping the container inside the legacy snapshot preserved on the virtual disk.

## Resolution
The application logic has been rewritten to target a separate environment variable path: `PERSISTENT_DIR` (resolving to `/data`). This allows the container's root directory (`/home/user/app`) to remain entirely ephemeral.

**Resulting Target State:**
- `app.py`, `schemas.py`, HTML Templates, CSS, and structural dependencies are executed flawlessly out of the latest GitHub commit built into the Docker image.
- Database reading/writing strictly scopes to the segmented `/data` volume.

**Status: ELIMINATED**
