"""
Script to update existing students with roll numbers
Format: MCA1001 for Year 1, MCA2001 for Year 2
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saara.settings')
django.setup()

from saara.erp.models import Student


def update_roll_numbers():
    """Update all existing students with roll numbers"""
    print("\n📝 Updating student roll numbers...")
    
    # Get all students grouped by department and year
    students_by_dept_year = {}
    
    for student in Student.objects.all().order_by('semester', 'first_name'):
        dept_code = student.department.dept_code if student.department else "UNK"
        year = student.year_of_study
        
        key = (dept_code, year)
        if key not in students_by_dept_year:
            students_by_dept_year[key] = []
        students_by_dept_year[key].append(student)
    
    # Assign roll numbers
    for (dept_code, year), students in students_by_dept_year.items():
        # Base number: 1001 for Year 1, 2001 for Year 2
        base_number = year * 1000 + 1
        
        for i, student in enumerate(students):
            roll_no = f"{dept_code}{base_number + i}"
            student.roll_no = roll_no
            student.save()
            print(f"   ✓ {roll_no}: {student.first_name} {student.last_name} ({dept_code} Year {year})")
    
    print(f"\n✅ Updated {Student.objects.count()} students with roll numbers!")
    
    # Summary
    print("\n📊 Summary:")
    for (dept_code, year), students in sorted(students_by_dept_year.items()):
        base = year * 1000 + 1
        end = base + len(students) - 1
        print(f"   {dept_code} Year {year}: {len(students)} students (Roll: {dept_code}{base}-{dept_code}{end})")


if __name__ == "__main__":
    update_roll_numbers()
