#QMS System
A 21 CFR Part 11 compliant quality management system (QMS) web app with adherence to ALCOA principles using compliant open-sourced components. It should be simple but robust and will be deployed on-premise.

##Preferred Architecture:
- To be deployed in Ubuntu 20.04.6 LTS Server
- Use podman containerization
- Use a modular approach
- Use PostgreSQL 18 as backend db
- Appropriate load balancing strategy for multiple users 
- Allow integration with Entra
- Electronic Signature Service
- Appropriate backup service

##4 Operational Modules
- A. Electronic Document Management System (EDMS)
- B. Quality Record Management (QRM)
- C. Training Record Management (TRM)
- D. Lab Information Management System (LIMS)

##Other Service Modules
- E. User Management
- F. Audit Trail
- G. Scheduler
- H. Backup and Health check
- I. App Settings

===== Service Modules ===============================================================================================================================
Service modules are only accessible to superusers and meant to provide cross-module services.

E. User Management
This module allows Admins for each Operational Modules to assign roles to users. Each operational module will have these permissions:
- read: all user should have at a minimum read access.
- write: allow user to create and edit entries + read
- review: allow user to review document + write
- approve: allow user to approve document + review
- admin: assign roles, reset passwords, add or remove users + approve

f. Audit Trail
In accordance to regulation, all modification to the database should be recorded. Add health check to ensure this essential function is online.

G. Scheduler
The Scheduler modules facilitates time-based events for the various modules. The superuser should have access to this module interface to view past tasks or upcoming task, stop or manually trigger a task. Again, any action that modifies the database should be recorded in the audit trial. Add health check to ensure this essential function is online.

H. Backup and Health check
The backup and health check module allows status check on the health of the various modules and the backup status of the database and essential env values to recreate the app in another instance. Ideally, the app should be backed up daily when usage is low. This module allows user to check various versions of the backups, and allow manual backup. This module allow superuser to load a backup file into a new instance to restore the app.

I. App Settings
The super user can change various settings in the app such as app banner, logo, etc.

===== Operational Modules ===========================================================================================================================
The operation module allows users to perform tasks for the various QMS functions.

----- A. Electronic Document Management System (EDMS) -----------------------------------------------------------------------------------------------
The EDMS provide a platform to (1) upload, (2) up-version and (3) obsoleting a document.

- Roles:
  1. Document Viewer (Base Permission: read)
  2. Document Author (Base Permission: write)
  3. Document Reviewer (Base Permission: review)
  4. Document Approver (Base Permission: approval)
  5. Document Admin (Base Permission: admin)

- Document Types:
  1. Policy
  2. Manual
  3. Procedures
  4. Work Instructions (SOP)
  5. Forms and Templates
  6. Records

- Document Source:
  1. Original Digital Draft: Original draft uploaded to EDMS in which upon approval, a digitally signed official PDF will be created.
  2. Scanned Original: A digital file created directly from the original physical document.
  3. Scanned Copy: A digital file created by scanning a paper photocopy of the original document. 

- Document Metadata:
  1. Document Number
  2. Version Number
  3. Document Title
  4. Document Type
  5. Document Source
  6. Document Dependencies
  7. Author
  8. Reviewer
  9. Approver
 10. Approval Date
 11. Effective Date
 12. Document Status
 13. Download Date
 14. Revision History

- Dashboard:
  Section 1. Shows documents that belongs to the user that are still in the workflow.
  Section 2. Shows approved documents, allow sorting and filltering, and allow viewing

- Workflows:
  
  1. Review Workflow:
     Start Review Workflow
     └──A user with at least write permission (author)  create a document placeholder where a document number is generated. (Document status: DRAFT)
        └──Author upload document and complete basic information such as (Title, Description, Document Type, Document Source, Document Dependencies (only approved and effective document), etc).
           └──Author select a reviewer and route to document for review. (Document status: Pending Review)
              └──Reviewer downloads document and provide comments.
                 ├──Reviewer Rejects document
                 │  └──Document return to Author for edit, re-upload, etc. (Document status: DRAFT)
                 └──Reviewer Approve document (Document status: Reviewed)
                    └──Author select an approver and route to document for approval. (Document status: Pending Approval)
                       └──Approver downloads document and provide comments.
                          ├──Approver Rejects document
                          │  └──Document return to Author for edit, re-upload, etc. (Document status: DRAFT)
                          └──Approver Approve document (Document status: Reviewed)
                             └──Approver select an effective date. (Document status: Approved, Pending Effective)
                                ├──End Workflow Review
                                └──Scheduler checks if effective date =< today.  (Document status: Approved and Effective)

  2. Up-versioning Workflow:
     Start up-versioning workflow on an Approved and Effective Document
     └──A user with at least write permission (author) initiate a up-versioning (increase minor version). Current approved and effective documents is still visible until workflow is completed.
        └──Author provide reason for the up-versioning.
        └──Author follows Review Workflow.
           ├──End up-versioning workflow (increase major version). Author and approver of documents that depends on the prior version will recieve notification to verify impact to dependent documents.
           └──Scheduler checks if effective date =< today.  (Set prior version to: Superseded; New approved document to: Approved and Effective)

  3. Obsolute Workflow:
     App checks for other approved document(s) which depends on an Approved and Effective Document targeted to be obsolute.
     ├──If there are dependent documents, prevent any user from initiating Obsolute Workflow.
     └──If there are no dependent documents, a user with at least write permission (author) enters reason to obsolute document.  
        └──Start obsoluting workflow
            └──Author initiate a obsolute workflow. Current approved and effective documents is still visible until workflow is completed.
               └──Author provide a reason for obsoluting document.
                  └──Author select an approver and route to document for approval.
                     └──Author select an approver and route to document for approval.
                        ├──Approver Rejects Obsoletion
                        │  └──No change to document.
                        └──Approver Approve Obsoletion (Document status: Pending Obsoletion)
                           └──Approver select an Obsoletion date. (Document status: Approved, Pending Effective)
                              └──Do final check if there are no document depending on target document
                                 ├──If there are dependent documents, terminate workflow.
                                 └──If there are no dependent documents, change document status to Pending Obsoletion. This prevents other workflows such as up-versioning and obsolute workflow and linking as depending document.
                                    └──Scheduler checks if effective date =< today.  (Document status: Obsoletion)

  4. Termination of Workflow:
     Author may terminate any workflow before approval by providing a reason. The document status return to its last approved state.

- Types of Downloads:
  1) Original Document: The original unmodified draft
  2) Annotated Document: The original document with appended meta data
  3) Official PDF: The annotated approved document converted to PDF and digitally signed

- Action Menu for Document Download
  ├──Download Original Document
  ├──Download Annotated Document
  │  ├──For .docx files
  │  │  └──find and replace special placeholders (indicated in the EDMS settings) with metadata of document such as document title, document number, version number, author, reviewer, approver, approved date, effective date, revision history, current status, downloaded date, etc.
  │  └──For other files
  │     └──download original document along with text file consisting of meta data.
  └──Action when downloading Official PDF:
     ├──For .docx files
     │  └──Generate Annotated Document
     │     └──Digitally Sign PDF for download
     └──For other files
        └──Convert file to PDF
           └──Annotate meta data
              └──Digitally Sign PDF for download

- Misc:
  A table of available metadata paired with the placeholder for search and replacement.  


----- B. Quality Record Management (QRM) ------------------------------------------------------------------------------------------------------------
The QRM allows user to (1) Report a quality event, (2) escalate it to Deviation or Investigation, (3) address it via CAPAs and (4) Initiate Change Control if required.

- Roles:
  1. Viewer (Base Permission: read)
  2. Responsible Person (Base Permission: write)
  3. Quality Reviewer (Base Permission: review)
  4. Quality Approver (Base Permission: approval)
  5. Quality Admin (Base Permission: admin)

- Dashboard:
  Section 1. Shows Quality Events, Deviations, Investigations, CAPA and Change Controls that involves the user that are still in the workflow.
  Section 2. Shows approved quality reports, allow sorting and filltering, and allow viewing

- Workflows:
  
  1. Quality Event Workflow:
     └──Responsible Person create a quality event placeholder required to complete with basic information (such as type of quality impact, serverity, etc.), chooses a quality reviewer and route it for review within 3 days of reporting. 
        └──Quality Reviewer will classify the quality event within 7 days of reporting.
           ├──If event have no quality impact, Quality reviewer may close it.
           ├──If event have quality impact with known root cause, Quality reviewer may escalate it to Deviation (to be closed within 30 days of reporting) and route it to a Responsible Person.
           │  └──Responsible Person will complete deviation report and route it to a Quality Reviewer
           │     ├──Quality Reviewer reject report
           │     │  └──Return deviation to responsible person to address deficiency. 
           │     └──Quality Reviewer accept report
           │        └──Responsible Person will route it to Quality Approver to Approve Report.
           │           ├──Quality Approver reject report
           │           │  └──Return deviation to responsible person to address deficiency. 
           │           └──Quality Approver accept report
           │              └──Deviation is closed.
           └──If event have quality impact with unknown root cause, Quality reviewer may escalate it to Investigation (to be closed within 90 days of reporting) and route it to a Responsible Person.
              └──Responsible Person will complete investigation report and route it to a Quality Reviewer
                 ├──Quality Reviewer reject report
                 │  └──Return investigation to responsible person to address deficiency. 
                 └──Quality Reviewer accept report
                    └──Responsible Person will route it to Quality Approver to Approve Report.
                       ├──Quality Approver reject report
                       │  └──Return investigation to responsible person to address deficiency. 
                       └──Quality Approver accept report
                          └──Investigation  is closed.

  2. CAPA Workflow
     └──Responsible Person create a CAPA plan based on a Closed Quality Event, Approved Deviation Report or Approved Investigation Report
        └──Responsible Person will complete CAPA plan and route it to a Quality Reviewer
           ├──Quality Reviewer reject plan
           │  └──Return CAPA plan to responsible person to address deficiency. 
           └──Quality Reviewer accept plan
              └──Responsible Person will route it to Quality Approver to Approve plan.
                 ├──Quality Approver reject plan
                 │  └──Return CAPA plan to responsible person to address deficiency. 
                 └──Quality Approver accept plan
                    └──CAPA plan is initiated.
                       └──Responsible Person will excecute the CAPA plan, complete the CAPA report and route it to a Quality Reviewer
                          ├──Quality Reviewer reject report
                          │  └──Return CAPA report to responsible person to address deficiency. 
                          └──Quality Reviewer accept report
                             └──Responsible Person will route it to Quality Approver to Approve report.
                                ├──Quality Approver reject report
                                │  └──Return CAPA report to responsible person to address deficiency. 
                                └──Quality Approver accept report
                                   └──CAPA is closed.

  3. Change Control Workflow
     └──Responsible Person initiate a Change Control Request
        └──Responsible Person will complete Change Control Request and evaluation (may add links to documents in EDMS, quality events, deviation or investigations) and route it to a Quality Reviewer
           ├──Quality Reviewer reject Change Control
           │  └──Return Change Control Request to responsible person to address deficiency. 
           └──Quality Reviewer accept Change Control Request
              └──Responsible Person will route it to Quality Approver to Approve request.
                 ├──Quality Approver reject request
                 │  └──Return Change Control Request to responsible person to address deficiency. 
                 └──Quality Approver accept request
                    └──Change Control is initiated.
                       └──Responsible Person will excecute the Change Control, complete the Change Control report and route it to a Quality Reviewer
                          ├──Quality Reviewer reject report
                          │  └──Return Change Control report to responsible person to address deficiency. 
                          └──Quality Reviewer accept report
                             └──Responsible Person will route it to Quality Approver to Approve report.
                                ├──Quality Approver reject report
                                │  └──Return Change Control report to responsible person to address deficiency. 
                                └──Quality Approver accept report
                                   └──Change Control is closed.

- Generation of quality reports:
  - Allow QMS users to generate individual or bulk reports for closed quality event, approved deviation report, approved investigation report, approved CAPA report and approved Change Control report.
  - Add download date and digitally sign before download. 

----- C. Training Record Management (TMS) ------------------------------------------------------------------------------------------------------------
The TMS allows training coordinator to (1) Build curriculum referencing documents in EDMS and (2) assign curriculum to trainees; trainee to (3) quickly recieve and track training progress and (4) upload training documents; (5) trigger retraining when new document version is approved.

- Roles:
  1. Trainee (Base Permission: write)
  2. Training Coordinator (Base Permission: write)
  3. Trainer (Base Permission: review)
  4. Manager (Base Permission: approval)
  5. Quality Admin (Base Permission: admin)

- Dashboard:
  Section 1. Shows incomplete trainings that are assigned to users.
  Section 2. Shows all training curriculum completed by user, allow sorting and filltering, and allow viewing

- Workflows:
  
  1. Training Workflow:
     └──Training Coordinator create a training syllabus for various purposes or activities. He may group various syllabus into curriculum.
        └──Training Coordinator may assign curriculum to trainee.
           └──Trainee may view the reading materials for each syllabus, after training (self reading or by trainer), trainee may mark activities as complete and link any any training records uploaded in EDMS.
              └──Upon completion of each syllabus, Trainee may send it to trainer for review
                 ├──Trainer reject training status
                 │  └──Return syllabus to trainee as incomplete. 
                 └──Trainer accept training status
                    └──Trainer will route it to Manager to Approve Training Status.
                       ├──Manager reject Training Status
                       │  └──Return syllabus to trainee as incomplete. 
                       └──Manager accept Training Status
                          └──Trainee is trained.

  2. Re-training Workflow for expired training:
     └──All trainee will have to be re-trained every 3 years.
        └──Scheduler will assign trainee with expiring syllabus one month in advance.
           └──Start Training Workflow
              └──End Training Workflow 
           
  3. Re-training Workflow for up-versioned document:
     └──All trainee that were assigned previous document version will have to be trained on the new document.
        └──Scheduler will assign trainee with new document version.
           └──Start Training Workflow
              └──End Training Workflow 

- Generation of training reports:
  - Allow QMS users to generate individual or bulk reports for training records for self.
  - Admin and Manager can generate bulk training record.
  - Add download date and digitally sign before download. 

----- D. Lab Information Management System (LIMS) ---------------------------------------------------------------------------------------------------
The LIMS provide a platform for lab users to track inventories (CofA, expiry date per lot), equipments (calibration record), assays (analyst, sample results and control results), sample lifecycle as well as CofA generation from assay results.

- Roles:
  1. Analyst (Base Permission: write)
  2. Sample Manager (Base Permission: write)
  3. Lab Reviewer (Base Permission: review)
  4. Lab Director (Base Permission: approval)
  5. Lab Admin (Base Permission: admin)

- Dashboard:
  Section 1. Shows incomming sample shipments, samples pending analysis.

- Workflows:
  
  1. Sample Lifecycle:
     - Recieving (sample manifest, Assign Sample ID)
     - Storage
     - Pending Analysis
     - Analyzed
     - Returned to storage
     - Disposal 
     
  2. Assay Registration:
     - Assay SOP (link in EDMS)
     - Assay Worksheet (link in EDMS)
     - Other Assay documents (link in EDMS)
     - Materials (link cat number in inventory)
     - Equipments (link equipments)
     - Required Training (link syllabus)
     - Specifications (link to Product ID)

  3. CofA Registration
     - Product ID
     - List of Required Assays 
     - Notes

  4. Sample Registration
     - List of samples
     - CofA
     - Input data, link data and analysis in EDMS

  5. CofA Generation
