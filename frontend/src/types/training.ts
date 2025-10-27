// Training Management System Types for QMS Platform v3.0

export interface TrainingRecord {
  id: string
  employee_id: string
  employee_name: string
  training_title: string
  training_type: 'initial' | 'refresher' | 'continuing' | 'specialized'
  status: 'scheduled' | 'in_progress' | 'completed' | 'expired' | 'overdue'
  scheduled_date: string
  completion_date?: string
  expiry_date?: string
  trainer: string
  score?: number
  certification_required: boolean
}

export interface Employee {
  id: string
  name: string
  email: string
  department: string
  jobRole: string
}

export interface DocumentReference {
  id: string
  title: string
  type: 'SOP' | 'Form' | 'Policy' | 'Manual' | 'Certificate' | 'Work Instruction'
  category: 'Reference Material' | 'Training Form' | 'Certificate Template'
}

export interface TrainingDashboardStats {
  totalPrograms: number
  activeAssignments: number
  completedThisMonth: number
  overdueTrainings: number
  complianceRate: number
}

// Form interfaces for component state
export interface ProgramFormData {
  title: string
  description: string
  type: string
  duration: string
  passingScore: string
  validityPeriod: string
  linkedDocuments: DocumentReference[]
  requireApproval: boolean
  sendReminders: boolean
  autoAttachDocuments: boolean
}

export interface AssignmentFormData {
  programId: string
  employeeIds: Employee[]
  dueDate: string
  notes: string
  notifyEmployees: boolean
  notifyManagers: boolean
}