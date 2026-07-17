-- 1. top 10 companies by net profit
select company_id, year, net_profit
from profitandloss
order by net_profit desc
limit 10;


-- 2. companies with highest sales
select company_id, year, sales
from profitandloss
order by sales desc
limit 10;


-- 3. average ROE by company
select company_id, avg(return_on_equity_pct) as avg_roe
from financial_ratios
group by company_id
order by avg_roe desc;


-- 4. companies with negative profit
select *
from profitandloss
where net_profit < 0;


-- 5. companies with high debt
select company_id, year, borrowings
from balancesheet
order by borrowings desc
limit 10;


-- 6. latest stock price per company
select company_id, max(date) as latest_date
from stock_prices
group by company_id;


-- 7. companies with low data coverage
select company_id, count(*) as years
from profitandloss
group by company_id
having count(*) < 5;


-- 8. check duplicate records (should be zero)
select company_id, year, count(*)
from profitandloss
group by company_id, year
having count(*) > 1;


-- 9. join example (profit + market cap)
select p.company_id, p.year, p.net_profit, m.market_cap_crore
from profitandloss p
join market_cap m
on p.company_id = m.company_id and p.year = m.year;


-- 10. high dividend companies
select company_id, year, dividend_payout
from profitandloss
order by dividend_payout desc
limit 10;
