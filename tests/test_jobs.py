def payload(count=2):
    return {
        "event_name": "Python Workshop", "event_date": "2026-10-07",
        "organization_name": "ABC Institute", "signatory_name": "Dr. John Doe",
        "recipients": [{"name": f"Person {i}", "email": f"person{i}@example.com", "certificate_id": f"CERT-{i:03d}"} for i in range(count)],
    }