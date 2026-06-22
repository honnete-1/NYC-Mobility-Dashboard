 # AI Use & Ethical Declaration Log

In accordance with academic integrity guidelines, this log documents the ethical use of Artificial Intelligence (AI) assistance during the design, implementation, and deployment of the **NYC Urban Mobility Dashboard** project.

---

## 1. Ethical Guidelines Followed
We adhered to the following core principles to ensure our use of AI was responsible, educational, and ethically compliant:

* **Student Ownership:** The core application architecture, database Star Schema model, data cleaning thresholds, and frontend design were decided and driven  by us me and Emmanuella

* **DSA Authenticity:** The custom Min-Heap data structure in `backend/algorithms.py` was implemented manually to meet the assignment requirements. AI was used only to verify mathematical complexity ($O(N \log K)$ vs $O(N \log N)$) and debug boundary conditions.

---

## 2. AI Tool & Usage Details

| Project Stage | Tasks Assisted by AI | Student Contribution & Validation | Ethical Justification |
| :--- | :--- | :--- | :--- |
| **ETL Pipeline & Data Cleaning** | Syntax suggestions for chunk-based CSV loading in Pandas to prevent out-of-memory crashes on large files. | Used as a productivity aid to handle massive dataset constraints. |
| **Database Design (Star Schema)** | Suggestions for optimal SQLite pragmas (`temp_store = MEMORY`, `journal_mode = WAL`) to speed up database queries. | Designed the relational tables (trips fact table and dimension lookups) and mapped out the Entity-Relationship Diagram (ERD). | Used for database performance optimization. |
| **Custom Algorithms (Min-Heap)** | Debugging assistance with array index math for binary tree navigation (parent/child node relationships) during sifting.  | Used as a tutoring tool to review index offsets. |
| **Frontend & Chart Customization** | Guidance on ApexCharts configuration syntax to enable dynamic redrawing when swapping styles. | Designed the HTML5 layout, CSS glassmorphism styles, and constructed the Light/Dark mode reactive variable systems. | Used for API documentation assistance. |
| **Deployment & Serverless Routing** | Debugging Vercel deployment folder path casing conflicts caused by Linux hosting environment case-sensitivity. | Configured `vercel.json` rewrites, managed Git branches, and verified live production links. | Used for DevOps debugging. |

---

## 3. Student Reflections on AI Integration
* **Honnete (Backend & DB):** 
  > *"Using AI helped me understand how SQLite handles temporary files under memory constraints. Instead of letting low disk space block my development, I used the AI to help me build a pure-Python simulation fallback, ensuring my ETL scripts could run on any hardware without crashing. It acted as an interactive tutor for data engineering."*

* **Emmanuella (Frontend & API):** 
  > *"The AI was useful for explaining how to dynamically update Chart colors in JavaScript without triggering page refreshes. It allowed me to focus on creating a premium user interface and fine-tuning our styling variables rather than spending hours digging through chart documentation."*

---

### **Declaration Statement**
We declare that this project represents our own original work. Where AI tools were utilized, they were used strictly as debugging assistants, and all final logic was fully understood, reviewed, and approved by us.

**Signed:**  
* Honnete Nishimwe  
* Emmanuella Gacuti  
* **Date:** June 21, 2026
