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
assert.ok(!fs.readFileSync(path.join(root,"app/web/app.js"),"utf8").includes("/api/v1/sync/"));
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
console.log("Frontend checks passed: four languages, translation coverage, preferences and concise affair fields.");
