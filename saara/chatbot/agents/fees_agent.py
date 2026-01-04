from saara.erp.models import StudentFees, FeeStructure


class FeesAgent:
    """Agent to handle fees-related queries"""
    
    def __init__(self, student):
        """
        Initialize with student instance
        Args:
            student: Student model instance
        """
        self.student = student

    def get_fees(self):
        """
        Get fee details for the student
        Returns:
            Dictionary with fee data
        """
        fees = StudentFees.objects.filter(student=self.student).select_related('fee')

        if not fees.exists():
            return {"error": "No fee records found."}

        total_paid = sum(float(f.amount_paid) for f in fees)
        total_due = sum(float(f.due_amount) for f in fees)
        
        # Get fee details
        fee_details = []
        for fee in fees:
            fee_structure = fee.fee
            fee_details.append({
                "fee_id": fee_structure.fee_id,
                "academic_year": fee_structure.academic_year,
                "semester": fee_structure.semester,
                "tuition_fees": float(fee_structure.tution_fees),
                "development_fees": float(fee_structure.development_fees),
                "total_amount": float(fee_structure.amount),
                "amount_paid": float(fee.amount_paid),
                "due_amount": float(fee.due_amount),
                "status": fee.status,
            })

        # Determine overall status
        if total_due == 0:
            overall_status = "All Clear"
        elif total_paid > 0 and total_due > 0:
            overall_status = "Partially Paid"
        else:
            overall_status = "Pending"

        return {
            "student_name": f"{self.student.first_name} {self.student.last_name}",
            "total_paid": round(total_paid, 2),
            "total_due": round(total_due, 2),
            "overall_status": overall_status,
            "fee_details": fee_details
        }
