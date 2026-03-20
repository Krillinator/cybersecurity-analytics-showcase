# Run NordPay Demo

## Clone Project

```bash
git clone <repo.git>
cd project
```

## Build image (docker)
```bash
docker build -t nordpay-demo .
```

```bash
docker run -p 8000:8000 nordpay-demo
```

## Company Incident - Visualized
Statistical data, side-by-side comparison

<img width="1400" height="600" alt="Figure_1" src="https://github.com/user-attachments/assets/2e66228f-b4fc-4234-9b0e-d932b68f7458" />

# NordPay Case

## Step 1 – Login

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alpha", "password": "alpha123"}'
```
Copy the access token.

Question:
What breaks best practice in the response?

Answer:
<details> A token valid for 30 days is not recommended.</details> 

---

## Step 2 – View Transactions

```bash
curl http://localhost:8000/transactions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Save the transaction_id for later.

---

## Step 3 – Refund

```bash
curl -X POST http://localhost:8000/refund \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"transaction_id":"tx_1001","amount":500}'
```

---

## Step 4 – Swagger

Open:
http://localhost:8000/docs

Question:
Can you find additional endpoints?

---

## Step 5 – Debug Endpoint

curl http://localhost:8000/debug/data

Question:
Can you find transaction_id values from other partners?

---

## Step 6 – Try Again

Use a transaction_id that does not belong to you.

```bash
curl -X POST http://localhost:8000/refund \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"transaction_id":"tx_2002","amount":1500}'
```

Question:
Should this be allowed?

---

## Summary

This is Broken Access Control.
<details> 
The system decides to process a refund after the token has been verified, the transaction has been retrieved, and basic checks on status and amount have passed. It relies on data from the request, mainly `transaction_id` and `amount`, as well as `partner_id` extracted from the token.


The problem is that while the system identifies which partner is making the request, it never verifies that the transaction actually belongs to that partner. There is no connection between the authenticated user and the resource being affected.

This is an example of Broken Access Control, where a user can perform actions on resources they are not authorized to access. In practice, this means a partner can submit a valid `transaction_id` and issue a refund on another partner’s transaction.

The system therefore violates the Zero Trust principle, as it assumes that an authenticated user is automatically allowed to perform the action, instead of verifying authorization for each request.

The key solution is to link the user to the resource. In this case, the system must not only identify the partner via the token, but also verify that the transaction belongs to that partner before processing the refund.

## Improvements

- Least privilege  
  A partner should only access and modify their own data  

- Validate all resource-related input  
  Always verify that `transaction_id` belongs to the requesting partner  

- Logging and monitoring  
  Detect unusual behavior such as multiple refund attempts  

- Manual review for sensitive operations  
  Refunds involve money and may require additional checks  

- Avoid exposing internal IDs  
  Or make them harder to guess  
</details>

Feel free to explore the repository and find additional 'problems' to solve!