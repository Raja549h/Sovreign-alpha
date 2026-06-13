from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://svrn-alpha-sovereignalpha.hf.space/_debug/edge', wait_until='networkidle', timeout=30000)

    ids = ['edgeScore', 'accuracyRate', 'weightedAccuracy', 'avgConfidence', 'totalObs',
           'confirmed', 'partial', 'invalidated', 'activeObs', 'monitoring',
           'bestCats', 'worstCats']

    print('=== EDGE DASHBOARD LIVE VALUES ===')
    for eid in ids:
        sel = '#' + eid
        el = page.query_selector(sel)
        val = el.text_content() if el else 'NOT FOUND'
        print(f'  {eid}: {val}')

    print()
    title = page.query_selector('h1')
    print('Page title:', title.text_content() if title else 'N/A')

    page.screenshot(path=r'C:\Users\lokes\Downloads\project\sovereign-alpha\edge_live.png', full_page=True)
    print('Screenshot saved')
    browser.close()
