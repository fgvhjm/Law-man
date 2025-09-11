# Setup Instructions

- The Docling is in the retrieve file.  
- To set up the project:
  1. Clone it.  
  2. Create a venv (see instructions online if you don’t know about venv).  
  3. Install requirements using the command:  
     ```bash
     pip install -r requirements.txt
     ```
  4. Create your own branch to commit or push.  
     - Please add a valid message and proper changes you have made or improved.

## docling input and output
  ##### input :- pdf ,scanned,images , text 
  ##### output 
  ###### json format
 - "contract_id": "contract.pdf",
  - "clause_id": "c3",
  - "heading": "COMPENSATION",
  - "text": "In consideration for CONSULTANT accomplishing said result...",
  - "page": 2,
     - "line_start": 15,
  - "line_end": 30,
     - "lang": "en"


 
