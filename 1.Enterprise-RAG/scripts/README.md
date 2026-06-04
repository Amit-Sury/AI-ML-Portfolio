# Python scripts

- 📁 File Organization

```
├── .env                             # environment variables 
├── __init__.py                      # exports dependent functions, classes
├── aws_utilities.py                 # aws utility functions
├── create_index.py                  # creates index in opensearch serverless collection 
├── gen_embedding.py                 # generates query embeddings
├── graph.py                         # langGraph workflow orchestration
├── guardrails_classes.py            # guardrails class definitions
├── guardrails_service.py            # implements input and output guardrails
├── init_llm.py                      # LLM initialization logic
├── rag_fastapi.py                   # entry point, defines all the fastapi endpoints
├── retrieval_service.py             # implements retrieval pipeline
├── startup.py                       # creates necessary resources for retrieval pipeline
├── ui_layout.py                     # html/css for UI
├── .dockerignore                    # exclude logs, history, .env, __pycache__, etc.
|── Dockerfile                       # eontainer build config
├── requirements.txt                 # dependencies
```
