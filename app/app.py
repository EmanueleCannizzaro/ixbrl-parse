from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import matplotlib.pyplot as plt
from pathlib import Path

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
Path("static/images").mkdir(parents=True, exist_ok=True)

def load_xbrl_data():
    try:
        with open("aapl.json", "r") as file:
            data = json.load(file)
        if not isinstance(data, dict) or 'xbrl_content' not in data:
            raise ValueError("Unexpected JSON structure")
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error decoding JSON: {str(e)}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="XBRL data file not found")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_facts(xbrl_data):
    facts = []
    for child in xbrl_data['xbrl_content']['children']:
        if 'tag' in child and 'attributes' in child:
            facts.append({
                'concept': child['tag'],
                'value': child.get('text', ''),
                'contextRef': child['attributes'].get('contextRef', ''),
                'unitRef': child['attributes'].get('unitRef', ''),
                'decimals': child['attributes'].get('decimals', '')
            })
    return facts

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        xbrl_data = load_xbrl_data()
        facts = xbrl_data['xbrl_content']['children']
        sector_avg = xbrl_data.get('sector_averages', {})

        ratios = calculate_financial_ratios(facts, sector_avg)
        european_metrics = calculate_european_metrics(facts, sector_avg)
        
        facts_data = extract_facts(xbrl_data)

        return templates.TemplateResponse("xbrl_data.html", {
            "request": request, 
            "data": xbrl_data,
            "ratios": ratios,
            "european_metrics": european_metrics,
            "sector_averages": sector_avg,
            "facts_data": facts_data
        })
    except HTTPException as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{e.detail}</p>", status_code=e.status_code)

def get_fact_value(facts, concept_name):
    for fact in facts:
        if concept_name.lower() in fact['tag'].lower():
            try:
                return float(fact['text'].replace(',', ''))
            except:
                return 0.0
    return 0

def create_comparison_chart(company_data, sector_avg, title):
    labels = list(company_data.keys())
    company_values = list(company_data.values())
    sector_values = [sector_avg.get(label, 0) for label in labels]  # Use .get() with a default value

    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar([i - width/2 for i in x], company_values, width, label='Company')
    ax.bar([i + width/2 for i in x], sector_values, width, label='Sector Average')

    ax.set_ylabel('Values')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()

    plt.tight_layout()
    plt.savefig(f'static/images/{title.lower().replace(" ", "_")}.png')
    plt.close()

def calculate_financial_ratios(facts, sector_avg):
    current_assets = get_fact_value(facts, 'CurrentAssets')
    current_liabilities = get_fact_value(facts, 'CurrentLiabilities')
    total_assets = get_fact_value(facts, 'Assets')
    total_liabilities = get_fact_value(facts, 'Liabilities')
    equity = get_fact_value(facts, 'Equity')
    net_income = get_fact_value(facts, 'ProfitLoss')
    revenue = get_fact_value(facts, 'Revenue')

    ratios = {
        'CurrentRatio': current_assets / current_liabilities if current_liabilities else 0,
        'DebtToEquityRatio': total_liabilities / equity if equity else 0,
        'ReturnOnAssets': net_income / total_assets if total_assets else 0,
        'ReturnOnEquity': net_income / equity if equity else 0,
        'ProfitMargin': net_income / revenue if revenue else 0
    }

    create_comparison_chart(ratios, sector_avg, 'Financial Ratios Comparison')

    return ratios

def calculate_european_metrics(facts, sector_avg):
    total_assets = get_fact_value(facts, 'Assets')
    current_assets = get_fact_value(facts, 'CurrentAssets')
    equity = get_fact_value(facts, 'Equity')
    revenue = get_fact_value(facts, 'Revenue')
    prior_year_revenue = get_fact_value(facts, 'PriorYearRevenue')
    
    metrics = {
        'AssetTurnover': revenue / total_assets if total_assets else 0,
        'WorkingCapital': current_assets - get_fact_value(facts, 'CurrentLiabilities'),
        'EquityRatio': equity / total_assets if total_assets else 0,
        'RevenueGrowth': (revenue - prior_year_revenue) / prior_year_revenue if prior_year_revenue else 0
    }

    create_comparison_chart(metrics, sector_avg, 'European Metrics Comparison')

    return metrics

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        xbrl_data = load_xbrl_data()
        facts = xbrl_data['xbrl_content']['children']
        sector_avg = xbrl_data.get('sector_averages', {})  # Use .get() with a default empty dict

        ratios = calculate_financial_ratios(facts, sector_avg)
        european_metrics = calculate_european_metrics(facts, sector_avg)

        return templates.TemplateResponse("xbrl_data.html", {
            "request": request, 
            "data": xbrl_data,
            "ratios": ratios,
            "european_metrics": european_metrics,
            "sector_averages": sector_avg  # Ensure this is passed to the template
        })
    except HTTPException as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{e.detail}</p>", status_code=e.status_code)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
