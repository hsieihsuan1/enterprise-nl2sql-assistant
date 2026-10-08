"""Known questions for deterministic, offline demonstrations, not general NL understanding."""
QUESTIONS = {
    "Quais foram os 5 maiores clientes por receita em 2024?": "SELECT customer_name, SUM(revenue) AS total_revenue FROM sales WHERE order_date >= DATE '2024-01-01' AND order_date < DATE '2025-01-01' GROUP BY customer_name ORDER BY total_revenue DESC LIMIT 5",
    "Mostre a evolução mensal de receita": "SELECT strftime(order_date, '%Y-%m') AS month, SUM(revenue) AS total_revenue FROM sales GROUP BY 1 ORDER BY 1",
    "Quais produtos tiveram menor margem média?": "SELECT product_name, AVG(margin) AS avg_margin FROM sales GROUP BY product_name ORDER BY avg_margin",
    "Compare receita e volume por cliente": "SELECT customer_name, SUM(revenue) AS total_revenue, SUM(volume) AS total_volume FROM sales GROUP BY customer_name ORDER BY total_revenue DESC",
}

def offline_sql(question: str) -> str:
    if question not in QUESTIONS:
        raise ValueError("Offline mode supports only the four documented demo questions. Enable LLM mode for arbitrary questions.")
    return QUESTIONS[question]
