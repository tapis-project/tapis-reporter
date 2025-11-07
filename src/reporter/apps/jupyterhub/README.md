# JupyterHub NGINX Log Analysis

## Typical Log Entries

**GET Request for an existing notebook**: `GET /user/<username>/notebooks/path/to/MyCoolNotebook.ipynb HTTP/1.1" 200`

**POST Request for creating a new notebook**: `POST /user/<username>/api/contents/ HTTP/1.1" 201`

**GET Request for loading a new notebook**: `GET /user/<username>/api/contents/Untitled.ipynb HTTP/1.1" 200`

**API Requests for the Kernel**: `POST /user/<username>/api/sessions HTTP/1.1" 201`

---
## When Someone Creates a Notebook
When a user **creates a new notebook**, the primary indicator is a POST request to the single-user server's contents API for file management:
* **Log Entry (Creation)**: `... POST /user/<username>/api/contents/ HTTP/1.1" 201 ...`
    * **Method**: `POST` (to create a new notebook or directory)
    * **Status**: `201` (Created)

This is immediately followed by the browser session **loading the new notebook**:
* **Log Entry (Loading)**: `... GET /user/<username>/api/contents/Untitled.ipynb HTTP/1.1" 200 ...`
    * **Method**: `GET` (loading a new notebook)
    * **Status**: `200` (Loaded)

---
## Regex for Notebook Creations
Regular expression to find the creation and loading of a new notebook.

### Regex Syntax
This regex allows us to search for `POST` requests to `/api/contents/` with a 201 status.

```sh
^.*?"POST /user/[^/]+/api/contents/.*? HTTP/1\.[01]" 201 .*$
```

This regex allows us to search for `GET` requests to `/api/contents` with a 200 status.

```sh
^.*?"GET /user/[^/]+/api/contents/.*?/Untitled\.ipynb\?.*? HTTP/1\.[01]" 200 .*$
```
---
## Logic for determining Notebook Creations
There are a small number of other activities that send `POST` requests to `/api/contents` that we want to make sure are filtered out when trying to count the number of created notebooks.

The logic used to detect a new notebook creation in the Nginx logs relies on identifying a two-step sequence of API requests originating from the same user session described above.

**Key Logical Principles**:
1. **Event Grouping (Using IP Address)**:
    * We used the **IP address** as the key to track sequences. This ensures both the `POST` (Creation) and the subsequent `GET` (Loading) requests came from the `same client browser instance` and are therefore related actions, improving accuracy.
2. **State Tracking**:
    * The script uses a dictionary to maintain a temporary state for each IP address.
    * When the script sees a `Creation`, it stores that log line.
    * It then checks if the very next relevant log line from the same IP is the `Loading`  event.
3. **Completion and Cleanup**:
    * Once a successful pair (Creation followed by Loading) is detected, the full log is saved.
    * The temporary state for that IP is then cleared to ensure the script doesn't try to link the initial creation event to any future, unrelated GET requests.
