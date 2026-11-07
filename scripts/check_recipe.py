from pathlib import Path
import re,json
root=Path(__file__).resolve().parents[1]
recipe=(root/'Dockerfile').read_text()
package=json.loads((root/'package.json').read_text())
lock=json.loads((root/'package-lock.json').read_text())
base=re.search(r'^FROM mcr.microsoft.com/playwright:v([^ -]+)-noble@sha256:([a-f0-9]{64}) AS runtime$',recipe,re.M)
assert base and package['dependencies']['playwright']==base[1]
assert lock['packages']['node_modules/playwright']['version']==base[1]
assert 'USER pwuser' in recipe and 'CMD ["src/demo.mjs"]' in recipe
assert recipe.index('USER pwuser')<recipe.index('FROM runtime AS verify')
assert 'RUN node src/browser-smoke.mjs' in recipe
assert (root/'src/demo.mjs').exists() and (root/'src/browser-smoke.mjs').exists()
assert (root/'.dockerignore').read_text().splitlines()==['*','!package.json','!package-lock.json','!src','!src/**']
print(json.dumps({'recipeContracts':'passed','playwrightPackageMatchesBase':True,'defaultFinalStage':'verify','containerBuildPerformed':False}))
