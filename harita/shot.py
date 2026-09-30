from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(args=['--allow-file-access-from-files'])
    pg=b.new_page(viewport={'width':4240,'height':2930})
    pg.goto('http://localhost:8777/compose.html')
    pg.wait_for_function("document.title=='ready'",timeout=60000)
    pg.wait_for_timeout(1500)
    pg.screenshot(path='/home/claude/work/mapgen/map_full.png')
    b.close()
