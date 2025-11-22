# 8. Customer Engagement Score

## Business Context

**Difficulty:** Advanced
**Use Case:** Customer Analytics / Retention / Segmentation
**Business Value:** This query creates a comprehensive engagement profile for each customer by analyzing their interaction patterns across different types of activities. It uses conditional aggregation (CASE statements) to break down interactions by type, providing insights into browsing behavior, purchase frequency, and support needs. Marketing teams use this to identify highly engaged customers for advocacy programs, detect at-risk customers with high support interaction, and personalize communication strategies based on engagement patterns.

## The Query

```sql
SELECT
    c.customer_id,
    c.name,
    c.segment,
    COUNT(DISTINCT i.interaction_id) as total_interactions,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'purchase' THEN i.interaction_id END) as purchases,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'view' THEN i.interaction_id END) as views,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'support' THEN i.interaction_id END) as support_tickets,
    AVG(i.duration_minutes) as avg_interaction_duration
FROM customers c
LEFT JOIN interactions i ON c.customer_id = i.customer_id
GROUP BY c.customer_id, c.name, c.segment
HAVING total_interactions > 0
ORDER BY total_interactions DESC
LIMIT 100;
```

## Expected Results

### Execution Metrics
- **Status:** Success
- **Execution Time:** 614.29 ms
- **Rows Returned:** 100 records
- **Data Processed:** Join between customers and interactions tables with conditional aggregation

### Sample Output

| customer_id | name              | segment | total_interactions | purchases | views  | support_tickets | avg_interaction_duration |
|-------------|-------------------|---------|-------------------|-----------|--------|-----------------|--------------------------|
| C-45892     | Sarah Mitchell    | VIP     | 2,847             | 142       | 2,678  | 27              | 3.45                     |
| C-23456     | James Patterson   | VIP     | 2,734             | 138       | 2,571  | 25              | 3.52                     |
| C-78901     | Emily Rodriguez   | VIP     | 2,689             | 145       | 2,523  | 21              | 3.38                     |
| C-34567     | Michael Chen      | Premium | 2,567             | 89        | 2,456  | 22              | 3.12                     |
| C-56789     | Jennifer Taylor   | VIP     | 2,534             | 147       | 2,362  | 25              | 3.48                     |

## Understanding the Results

### For Beginners

This query reveals which customers are most actively engaged with your business by counting all their interactions and breaking them down by type. Think of it as a customer activity report card that shows who's most involved with your brand across all touchpoints.

Let's examine Sarah Mitchell's profile: she has 2,847 total interactions, consisting of 142 purchases, 2,678 views, and 27 support tickets. This tells a clear story - she's a highly engaged customer who frequently browses your site (views), converts those views into purchases at a healthy rate (142 purchases), and occasionally needs support (27 tickets over her customer lifetime).

The ratio between different interaction types reveals important insights. Sarah has a view-to-purchase ratio of about 19:1 (2,678 views / 142 purchases), which means for every 19 times she browses, she makes 1 purchase. This is actually quite healthy - engaged customers often research extensively before buying. Her support ticket count (27) relative to purchases (142) means roughly 1 in 5 purchases requires some assistance, which might indicate opportunities to improve product descriptions or checkout flows.

Compare this to Michael Chen, a Premium customer with 2,567 total interactions but only 89 purchases. His view-to-purchase ratio is much higher (27:1), suggesting he's an engaged browser but less decisive buyer. This profile indicates someone who could benefit from targeted conversion strategies like limited-time offers or personalized product recommendations.

The avg_interaction_duration column shows how long customers typically spend on each interaction. Higher values (3-4 minutes) suggest engaged, deliberate browsing and purchasing. Very low values might indicate quick, transactional interactions without deeper engagement.

### Technical Deep Dive

This query demonstrates advanced SQL techniques: LEFT JOIN to preserve customers without interactions, conditional aggregation using COUNT(DISTINCT CASE WHEN...), multiple aggregate functions in a single query, and filtering on aggregated results with HAVING. The execution time of 614.29ms reflects the complexity of joining customers to potentially millions of interaction records.

ClickHouse optimizes this through several mechanisms. The LEFT JOIN likely uses hash join strategy, building a hash table of customer_id values. The conditional COUNT with CASE statements is executed using vectorized processing - ClickHouse evaluates the CASE condition in parallel across batches of rows and maintains separate counters for each interaction type.

The COUNT(DISTINCT ...) operations are the most expensive part, requiring hash sets to track unique interaction IDs per customer per type. For highly engaged customers with thousands of interactions, these hash sets consume significant memory. However, the LIMIT 100 enables early termination once top 100 customers are identified.

Performance characteristics: This query scales with total interaction count and the number of interactions per customer. Customers with 3,000 interactions require processing 3,000 records and maintaining multiple hash sets. The HAVING clause filters out customers with zero interactions, which might be 10-20% of the customer base (newly registered, inactive accounts).

Optimization opportunities: For production dashboards, add a date filter on interactions to focus on recent activity: `WHERE i.interaction_date >= today() - INTERVAL 90 DAY`. This could reduce execution time from 614ms to 50-100ms. Create a materialized view that incrementally maintains engagement scores. Consider pre-computing interaction counts in a summary table that updates nightly. Use approximate distinct counts (uniqHLL) for 3-5x performance improvement with minimal accuracy loss.

## Business Insights

### Key Findings
Based on the actual execution results:
- Successfully analyzed engagement patterns for 100 most-active customers in 614.29ms
- Top engaged customers show 2,500-2,800 total interactions, dominated by views (90%+) with smaller but significant purchase counts
- Purchase counts for top customers range from 89-147, indicating these are not just browsers but active buyers
- Support ticket ratios (20-27 tickets per customer) suggest ~15-20% of purchases require some form of assistance

### Actionable Recommendations

1. **VIP Advocacy Program**: Customers with 2,000+ interactions and 100+ purchases are your superfans. Recruit them for customer advisory boards, beta testing programs, testimonials, and referral incentives. Their deep engagement makes them ideal brand ambassadors.

2. **Support Reduction Initiative**: The 15-20% support contact rate per purchase indicates friction points. Analyze common support tickets for these high-engagement customers to identify systemic issues - if VIP customers need help, imagine how much worse it is for less-engaged users.

3. **Engagement-Based Segmentation**: Consider adding an "engagement tier" orthogonal to spend-based segments. A Premium customer with 2,500+ interactions is more valuable long-term than a VIP customer with only 500 interactions, even if current LTV is lower.

4. **Conversion Optimization for Browsers**: Customers with high view counts but lower purchase counts (like Michael Chen: 2,456 views, 89 purchases) need conversion assistance. Implement: abandoned browse emails, "you viewed this product" reminders, scarcity signals ("only 3 left"), and personalized discounts.

5. **Engagement Monitoring & Alerts**: Track interaction velocity - if a normally high-engagement customer (2,000+ interactions historically) shows declining activity (e.g., no interactions in 14 days), trigger intervention campaigns immediately. Early detection prevents churn.

6. **Duration Analysis**: Customers with avg_interaction_duration below 2 minutes may be experiencing site performance issues, finding navigation difficult, or bouncing due to unmet expectations. Conduct UX research on low-duration, high-interaction customers.

7. **Purchase Frequency Programs**: Top customers average 100-150 purchases. Create milestone programs (50th purchase bonus, 100th purchase VIP gift) to recognize and encourage continued engagement. Gamification of purchase milestones can increase frequency.

## Related Queries
- **Query 7**: Interaction Patterns by Type - See aggregate interaction patterns across all customers
- **Query 5**: Customer Purchase Behavior - Detailed purchase analysis for these engaged customers
- **Query 15**: Recent Customer Activity - Check recency of engagement for these top customers

## Try It Yourself

```bash
# Connect to ClickHouse
clickhouse-client --host localhost --port 9000

# Run the query
SELECT
    c.customer_id,
    c.name,
    c.segment,
    COUNT(DISTINCT i.interaction_id) as total_interactions,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'purchase' THEN i.interaction_id END) as purchases,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'view' THEN i.interaction_id END) as views,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'support' THEN i.interaction_id END) as support_tickets,
    AVG(i.duration_minutes) as avg_interaction_duration
FROM customers c
LEFT JOIN interactions i ON c.customer_id = i.customer_id
GROUP BY c.customer_id, c.name, c.segment
HAVING total_interactions > 0
ORDER BY total_interactions DESC
LIMIT 100;

# Optional: Focus on recent 90 days for faster results
SELECT
    c.customer_id,
    c.name,
    c.segment,
    COUNT(DISTINCT i.interaction_id) as total_interactions,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'purchase' THEN i.interaction_id END) as purchases,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'view' THEN i.interaction_id END) as views,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'support' THEN i.interaction_id END) as support_tickets,
    AVG(i.duration_minutes) as avg_interaction_duration
FROM customers c
LEFT JOIN interactions i ON c.customer_id = i.customer_id
WHERE i.interaction_date >= today() - INTERVAL 90 DAY
GROUP BY c.customer_id, c.name, c.segment
HAVING total_interactions > 0
ORDER BY total_interactions DESC
LIMIT 100;

# Optional: Calculate engagement scores with weighting
SELECT
    c.customer_id,
    c.name,
    c.segment,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'purchase' THEN i.interaction_id END) * 10 +
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'view' THEN i.interaction_id END) * 1 +
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'support' THEN i.interaction_id END) * -2 as engagement_score
FROM customers c
LEFT JOIN interactions i ON c.customer_id = i.customer_id
GROUP BY c.customer_id, c.name, c.segment
HAVING engagement_score > 0
ORDER BY engagement_score DESC
LIMIT 100;
```
