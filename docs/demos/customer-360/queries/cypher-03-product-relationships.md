# 3. Product Relationships

## Business Context

**Difficulty:** Beginner
**Graph Pattern:** Simple node lookup with filtering
**Use Case:** Product Catalog, Inventory Management
**Business Value:** This query demonstrates basic node filtering without relationship traversal - a building block for understanding product inventory and availability. While it doesn't showcase graph advantages yet, it establishes the foundation for product-centric queries that will later explore relationships between products, categories, and purchasing patterns.

## The Query

```cypher
MATCH (p:Product)
WHERE p.category = 'Electronics'
RETURN p.name, p.brand, p.price, p.stock_quantity
LIMIT 50;
```

## Graph Visualization Concept

This query selects individual Product nodes without following relationships. In a visualization, you would see 50 disconnected product nodes in the Electronics category, like islands in an ocean. This is essentially a filtered node lookup - the graph equivalent of a SQL SELECT from a single table. The real power comes when you extend this pattern to include relationships to customers, categories, or other products.

## Expected Results

### Execution Metrics
- **Status:** Skipped (mock mode - no database connection)
- **Expected Execution Time:** 25-50ms (label scan with property filter)
- **Expected Rows:** Up to 50 products
- **Hops/Depth:** 0 (no relationship traversal)

### Sample Output

| name | brand | price | stock_quantity |
|------|-------|-------|----------------|
| iPhone 15 Pro | Apple | 1199.00 | 45 |
| Samsung Galaxy S24 | Samsung | 999.00 | 67 |
| MacBook Pro 16" | Apple | 2499.00 | 23 |
| Sony WH-1000XM5 Headphones | Sony | 399.00 | 89 |
| Dell XPS 15 Laptop | Dell | 1799.00 | 34 |
| iPad Air | Apple | 599.00 | 112 |
| LG OLED TV 55" | LG | 1299.00 | 18 |
| Nintendo Switch | Nintendo | 299.00 | 156 |

## Understanding the Results

### For Beginners

This query is a simple lookup - similar to what you would do in SQL. We're asking for all Product nodes that have a category property set to 'Electronics', and we want to see their name, brand, price, and stock quantity.

Think of nodes in a graph database as smart objects that can have properties (name, price, brand) and can be connected to other nodes through relationships. In this query, we're not using any relationships yet - we're just filtering and retrieving nodes based on their properties.

The MATCH clause tells the database "find me nodes labeled as Product". The WHERE clause adds a filter "but only those in the Electronics category". The RETURN clause specifies which properties we want to see. The LIMIT 50 prevents overwhelming results if your Electronics catalog has thousands of items.

While this query doesn't demonstrate graph advantages yet, it's important for several reasons. First, it shows how to filter nodes by their properties - a fundamental skill. Second, it returns data that can be used as starting points for graph traversals. You might run this query to find a specific product, then use that product in a more complex query to find customers who bought it or related products that are frequently purchased together.

In a real application, this query might power a product catalog page where users browse Electronics. The results would show available products with pricing and stock information, helping customers make purchasing decisions.

### Technical Deep Dive

This query performs a label scan with property filtering. The execution plan would be: (1) Scan all nodes with the Product label, (2) Filter where category='Electronics', (3) Return specified properties, (4) Limit to 50 results.

For optimal performance, create a composite index on Product.category:
```cypher
CREATE INDEX FOR (p:Product) ON (p.category);
```

With this index, the database can skip the label scan and jump directly to Electronics products, reducing query time from O(n) where n=all products to O(log n) + O(k) where k=Electronics products.

Property access in graph databases is typically column-store optimized. Properties are stored separately from the graph structure, so retrieving p.name, p.brand, p.price, p.stock_quantity requires seeking to four different property stores. However, modern graph databases use compression and caching to make this efficient.

The LIMIT clause is evaluated after filtering but before property retrieval, so the database doesn't waste time fetching properties for products that won't be returned. This is similar to SQL's LIMIT behavior.

While this query doesn't require relationship traversal, it's often combined with patterns in more complex queries:
```cypher
MATCH (p:Product)-[:IN_CATEGORY]->(cat:Category {name: 'Electronics'})
MATCH (p)<-[:PURCHASED]-(c:Customer)
RETURN p.name, p.price, COUNT(c) as popularity
ORDER BY popularity DESC
LIMIT 50;
```

This extended version finds popular products by counting customers who purchased them - something that showcases graph advantages much more clearly.

## Business Insights

### Graph-Specific Advantages

1. **Property-Rich Nodes**: Unlike relational databases where adding properties requires schema changes, graph nodes can have different property sets. Some products might have warranty_years, others have perishable_date - the schema is flexible.

2. **Foundation for Traversal**: This simple query becomes powerful when extended with relationships. Want to find customers who bought these Electronics products? Just add `MATCH (p)<-[:PURCHASED]-(c:Customer)`.

3. **No Table Scans**: With proper indexes, node lookups by property are as fast as primary key lookups in SQL, but with the added benefit of being able to traverse to related data instantly.

### Key Findings

Typical Electronics catalog patterns:
- **Price Distribution**: Electronics products typically range from $50 (accessories) to $3,000+ (high-end laptops/TVs)
- **Brand Concentration**: 60-70% of Electronics are from top brands (Apple, Samsung, Sony, Dell, LG)
- **Inventory Patterns**: High-turnover items (phones, tablets) have lower stock quantities with more frequent replenishment
- **Category Breadth**: Electronics spans computing, mobile, audio, video, gaming - very diverse

### Actionable Recommendations

1. **Inventory Optimization**: Products with stock_quantity < 20 may need reordering, especially if they're popular items
2. **Pricing Strategy**: Analyze price distribution to identify gaps or opportunities for new product introductions
3. **Brand Performance**: Track which brands have the most SKUs and which are most profitable
4. **Product Graph Foundation**: Use this data to build richer product graphs by adding relationships to categories, brands, suppliers

## Comparison to SQL

**SQL Equivalent:**
```sql
SELECT name, brand, price, stock_quantity
FROM products
WHERE category = 'Electronics'
LIMIT 50;
```

**Is This Query Better in Cypher?**
For this simple query, SQL and Cypher are essentially equivalent in performance and expressiveness. The advantage of Cypher emerges when you extend the query to include relationships:

**Cypher Extension (easy):**
```cypher
MATCH (p:Product {category: 'Electronics'})<-[:PURCHASED]-(c:Customer)
RETURN p.name, COUNT(c) as buyers
ORDER BY buyers DESC
LIMIT 50;
```

**SQL Extension (complex):**
```sql
SELECT p.name, COUNT(DISTINCT c.customer_id) as buyers
FROM products p
LEFT JOIN purchases pur ON p.product_id = pur.product_id
LEFT JOIN customers c ON pur.customer_id = c.customer_id
WHERE p.category = 'Electronics'
GROUP BY p.product_id, p.name
ORDER BY buyers DESC
LIMIT 50;
```

The Cypher version simply adds one more pattern to the MATCH clause, while SQL requires JOINs and GROUP BY.

## Related Queries

1. **Query 5: Product Affinity** - Extends this by finding products frequently bought together
2. **Query 12: Most Popular Products by Segment** - Uses product filtering with customer relationships
3. **Query 6: Category Expansion** - Analyzes cross-category purchase patterns

## Try It Yourself

```bash
# Via PuppyGraph Web UI (http://localhost:8081)

MATCH (p:Product)
WHERE p.category = 'Electronics'
RETURN p.name, p.brand, p.price, p.stock_quantity
LIMIT 50;

# Try variations:

# 1. Find high-value Electronics:
MATCH (p:Product)
WHERE p.category = 'Electronics' AND p.price > 1000
RETURN p.name, p.brand, p.price
ORDER BY p.price DESC;

# 2. Low stock Electronics:
MATCH (p:Product)
WHERE p.category = 'Electronics' AND p.stock_quantity < 30
RETURN p.name, p.brand, p.stock_quantity
ORDER BY p.stock_quantity ASC;

# 3. Brand analysis:
MATCH (p:Product)
WHERE p.category = 'Electronics'
RETURN p.brand, COUNT(p) as product_count, AVG(p.price) as avg_price
ORDER BY product_count DESC;

# 4. Price ranges:
MATCH (p:Product)
WHERE p.category = 'Electronics'
RETURN
    CASE
        WHEN p.price < 100 THEN 'Budget'
        WHEN p.price < 500 THEN 'Mid-Range'
        WHEN p.price < 1500 THEN 'Premium'
        ELSE 'Luxury'
    END as price_tier,
    COUNT(p) as product_count
ORDER BY price_tier;
```


---

**Navigation:** [← Demo Guide](../README.md) | [All Cypher Queries](../CYPHER-QUERIES.md) | [Docs Home](../../../README.md)
