const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const storage = new Map();
const context = vm.createContext({window:{},localStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)}});
vm.runInContext(fs.readFileSync(path.join(root,"app/web/i18n.js"),"utf8"),context);
const ui=context.window.PolitUI;
assert.equal(JSON.stringify(ui.languages),JSON.stringify(["de","fr","it","en"]));
for(const [key,translations] of Object.entries(ui.translations))for(const language of ui.languages)assert.ok(translations[language],`${key}: missing ${language}`);
const html=fs.readFileSync(path.join(root,"app/web/index.html"),"utf8");
for(const match of html.matchAll(/data-i18n(?:-aria|-placeholder)?="([^"]+)"/g))assert.ok(ui.translations[match[1]],`Missing HTML translation: ${match[1]}`);
assert.ok(!html.includes("sync-open"));
const modules=["core","search","detail","account","subscriptions","ask","app"];
for(const name of modules){
  const source=fs.readFileSync(path.join(root,`app/web/${name}.js`),"utf8");
  assert.ok(!source.includes("/api/v1/sync/"),`${name}.js must not call the admin sync API`);
  assert.ok(!/\binnerHTML\b|insertAdjacentHTML|document\.write/.test(source),`${name}.js must build DOM nodes, not HTML strings`);
  assert.ok(html.includes(`/assets/${name}.js`),`${name}.js is not loaded by index.html`);
}
assert.ok(html.indexOf("/assets/core.js")<html.indexOf("/assets/search.js")&&html.indexOf("/assets/ask.js")<html.indexOf("/assets/app.js"),"core.js must load first and app.js last");
assert.equal(ui.readLanguage(),"de");ui.saveLanguage("fr");assert.equal(ui.readLanguage(),"fr");ui.saveLanguage("rm");assert.equal(ui.readLanguage(),"de");
const record={id:203543,body_id:263,body_key:"NW",external_id:"101053",created_at:"2025-08-14",updated_at:"2026-07-27",number:"2023.NWLR.655",title_de:"Alpinen Photovoltaik-Anlagen",type_harmonized_de:"Interpellation",type_harmonized_fr:"Interpellation",type_harmonized_it:"interpellanza",type_harmonized_en:"Interpellation",state_name_de:"Beantwortet",begin_date:"2023-04-04"};
for(const language of ui.languages){
  const fields=ui.detailFields("affairs",record,{canton:"NW"},language);
  assert.equal(fields.filter(([key])=>key==="type").length,1);
  assert.ok(!fields.some(([key])=>["id","body_id","external_id","created_at","updated_at"].includes(key)));
  assert.equal(ui.localized(record,"title",language),record.title_de);
  assert.equal(Object.keys(ui.datasets(language)).length,9);
}
assert.equal(ui.t("en","renewable_electricity"),"Renewable electricity");
assert.equal(ui.t("fr","page",{page:2,pages:4}),"Page 2 sur 4");
vm.runInContext(fs.readFileSync(path.join(root,"app/web/core.js"),"utf8"),context);
vm.runInContext(`window.Polit.state.categories=[{code:"climate_energy",name_de:"Klima & Energie",name_fr:"Climat & énergie",subcategories:[{code:"climate_energy_other",name_de:"Sonstiges",name_fr:"Autres"}]}];var categoryPath=window.Polit.categoryPath;`,context);
assert.equal(vm.runInContext('categoryPath({code:"climate_energy_other",name:"Sonstiges"})',context),"Klima & Energie / Sonstiges");
assert.equal(vm.runInContext('categoryPath({code:"other",name:"Sonstiges"})',context),"Sonstiges");
assert.equal(vm.runInContext('window.Polit.state.language="fr";categoryPath({code:"climate_energy_other"})',context),"Climat & énergie / Autres");
assert.equal(vm.runInContext('window.Polit.recordTitle("documents",{title:"Bericht",context_title:"Klimaschutz"})',context),"Bericht · Klimaschutz");
assert.equal(vm.runInContext('window.Polit.recordTitle("affairs",{title:"Bericht",context_title:"Klimaschutz"})',context),"Bericht");
console.log("Frontend checks passed: four languages, translation coverage, preferences, module structure and concise affair fields.");
