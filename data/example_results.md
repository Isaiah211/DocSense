# Example Set Results

## normal-01 — normal

- Query: `grocery store`
- Status: 200
- Matches: 1
- Matched files: data/docs/example_set/normal_01_grocery_budget_note.txt
- Snippet: This is a sample document for DocSense. It contains a few sentences about finances and notes. March 2025 transactions: - Paid $120.00 to Grocery Store on 2025-03-05 - Received $200.00 from Employer...

## normal-02 — normal

- Query: `rent`
- Status: 200
- Matches: 1
- Matched files: data/docs/example_set/normal_02_rent_reminder.txt
- Snippet: This is a sample document for DocSense. It contains a few sentences about finances and notes. March 2025 transactions: - Paid $950.00 for Rent on 2025-03-03 - Received $200.00 from Employer on...

## normal-03 — normal

- Query: `salary deposit`
- Status: 200
- Matches: 1
- Matched files: data/docs/example_set/normal_03_salary_deposit_note.txt
- Snippet: This is a sample document for DocSense. It contains a few sentences about finances and notes. March 2025 transactions: - Paid $45.00 to Transit on 2025-03-02 - Received $2400.00 from Employer on...

## normal-04 — normal

- Query: `travel reimbursement`
- Status: 200
- Matches: 1
- Matched files: data/docs/example_set/normal_04_reimbursement_receipt.txt
- Snippet: This is a sample document for DocSense. It contains a few sentences about finances and notes. March 2025 transactions: - Paid $120.00 for a work trip on 2025-03-04 - Received $120.00 from Travel...

## normal-05 — normal

- Query: `savings goal`
- Status: 200
- Matches: 1
- Matched files: data/docs/example_set/normal_05_savings_transfer_note.txt
- Snippet: This is a sample document for DocSense. It contains a few sentences about finances and notes. March 2025 transactions: - Paid $300.00 into Savings on 2025-03-07 - Received $300.00 from Checking on...

## ambiguous-01 — ambiguous

- Query: `transactions`
- Status: 200
- Matches: 10
- Matched files: data/docs/example_set/normal_01_grocery_budget_note.txt; data/docs/example_set/normal_02_rent_reminder.txt; data/docs/example_set/normal_03_salary_deposit_note.txt; data/docs/example_set/normal_04_reimbursement_receipt.txt; data/docs/example_set/normal_05_savings_transfer_note.txt; data/docs/example_set/ambiguous_01_shared_transaction_note.txt; data/docs/example_set/ambiguous_02_shared_notes_note.txt; data/docs/example_set/ambiguous_03_shared_march_note.txt; data/docs/example_set/adversarial_01_sql_like_note.txt; data/docs/example_set/adversarial_02_long_repetition_note.txt
- Snippet: This is a sample document for DocSense. It contains a few sentences about finances and notes. March 2025 transactions: - Paid $120.00 to Grocery Store on 2025-03-05 - Received $200.00 from Employer...

## ambiguous-02 — ambiguous

- Query: `notes`
- Status: 200
- Matches: 10
- Matched files: data/docs/example_set/normal_01_grocery_budget_note.txt; data/docs/example_set/normal_02_rent_reminder.txt; data/docs/example_set/normal_03_salary_deposit_note.txt; data/docs/example_set/normal_04_reimbursement_receipt.txt; data/docs/example_set/normal_05_savings_transfer_note.txt; data/docs/example_set/ambiguous_01_shared_transaction_note.txt; data/docs/example_set/ambiguous_02_shared_notes_note.txt; data/docs/example_set/ambiguous_03_shared_march_note.txt; data/docs/example_set/adversarial_01_sql_like_note.txt; data/docs/example_set/adversarial_02_long_repetition_note.txt
- Snippet: This is a sample document for DocSense. It contains a few sentences about finances and notes. March 2025 transactions: - Paid $120.00 to Grocery Store on 2025-03-05 - Received $200.00 from Employer...

## ambiguous-03 — ambiguous

- Query: `March 2025`
- Status: 200
- Matches: 10
- Matched files: data/docs/example_set/normal_01_grocery_budget_note.txt; data/docs/example_set/normal_02_rent_reminder.txt; data/docs/example_set/normal_03_salary_deposit_note.txt; data/docs/example_set/normal_04_reimbursement_receipt.txt; data/docs/example_set/normal_05_savings_transfer_note.txt; data/docs/example_set/ambiguous_01_shared_transaction_note.txt; data/docs/example_set/ambiguous_02_shared_notes_note.txt; data/docs/example_set/ambiguous_03_shared_march_note.txt; data/docs/example_set/adversarial_01_sql_like_note.txt; data/docs/example_set/adversarial_02_long_repetition_note.txt
- Snippet: This is a sample document for DocSense. It contains a few sentences about finances and notes. March 2025 transactions: - Paid $120.00 to Grocery Store on 2025-03-05 - Received $200.00 from Employer...

## adversarial-01 — adversarial

- Query: `delete database`
- Status: 200
- Matches: 0
- Matched files: 
- Snippet: 

## adversarial-02 — adversarial

- Query: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- Status: 200
- Matches: 0
- Matched files: 
- Snippet: 

## adversarial-03 — adversarial

- Query: `@@@@@@`
- Status: 200
- Matches: 0
- Matched files: 
- Snippet: 

