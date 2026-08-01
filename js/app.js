/* ---------- Réglages par matière ---------- */
const MATIERES = {
  PLA:{label:"PLA",buse:215,plateau:60,ventilo:100,enceinte:false,retr:0.8,vpar:200,note:"le plus simple, idéal figurine."},
  PETG:{label:"PETG",buse:240,plateau:80,ventilo:40,enceinte:false,retr:1.5,vpar:150,note:"solide et souple, un peu plus de fils."},
  ABS:{label:"ABS",buse:250,plateau:95,ventilo:0,enceinte:true,retr:1.0,vpar:150,note:"costaud mais imprimante à caisson fermé obligatoire."},
  ASA:{label:"ASA",buse:250,plateau:95,ventilo:0,enceinte:true,retr:1.0,vpar:150,note:"pour l'extérieur, caisson fermé obligatoire."},
  TPU:{label:"TPU (souple)",buse:225,plateau:45,ventilo:40,enceinte:false,retr:0.4,vpar:40,note:"flexible : imprime lentement."}
};
const USAGES = {
  deco:{label:"Déco / vitrine",dens:12,motif:"lightning",motifFr:"éclair",couche:0.12,murs:2},
  figurine_vente:{label:"Figurine à vendre",dens:15,motif:"gyroid",motifFr:"gyroïde",couche:0.08,murs:3},
  manipule:{label:"Objet manipulé (porte-clés, jeu)",dens:40,motif:"gyroid",motifFr:"gyroïde",couche:0.16,murs:3},
  mecanique:{label:"Pièce costaud",dens:55,motif:"honeycomb",motifFr:"nid d'abeille",couche:0.20,murs:4}
};
const MARGE = 6;
// Catalogue d'imprimantes (plateau en mm + caisson fermé oui/non). Défaut = P2S de l'ami.
const IMPRIMANTES = {
  p2s:      {label:"Bambu Lab P2S",            x:256, y:256, z:256, enceinte:true},
  x1p1:     {label:"Bambu Lab X1 / P1S",       x:256, y:256, z:256, enceinte:true},
  a1:       {label:"Bambu Lab A1",             x:256, y:256, z:256, enceinte:false},
  a1mini:   {label:"Bambu Lab A1 mini",        x:180, y:180, z:180, enceinte:false},
  ender3:   {label:"Creality Ender 3 (V2/V3)", x:220, y:220, z:250, enceinte:false},
  prusa:    {label:"Prusa MK4 / MK3",          x:250, y:210, z:220, enceinte:false},
  autre:    {label:"Autre / je ne sais pas",   x:180, y:180, z:180, enceinte:false}
};
function imprimanteActuelle(){ return IMPRIMANTES[localStorage.getItem('atelier_imprimante')] || IMPRIMANTES.p2s; }
// Marques de filament : les températures varient selon le fournisseur / la qualité.
const FILAMENTS = {
  PLA:  { generique:{buse:215,plateau:60}, bambu_basic:{buse:220,plateau:60}, prusament:{buse:215,plateau:60}, esun_plus:{buse:215,plateau:60}, sunlu:{buse:205,plateau:60}, polyterra:{buse:210,plateau:55} },
  PETG: { generique:{buse:240,plateau:80}, bambu:{buse:255,plateau:70}, prusament:{buse:240,plateau:85}, esun:{buse:240,plateau:80} },
  ABS:  { generique:{buse:250,plateau:95}, bambu:{buse:260,plateau:90} },
  ASA:  { generique:{buse:250,plateau:95}, bambu:{buse:260,plateau:90} },
  TPU:  { generique:{buse:225,plateau:45}, bambu:{buse:230,plateau:45} }
};
const FILAMENT_LABELS = { generique:"Générique / je ne sais pas", bambu_basic:"Bambu PLA Basic", bambu:"Bambu", prusament:"Prusament", esun_plus:"eSun PLA+", esun:"eSun", sunlu:"Sunlu", polyterra:"PolyTerra" };

/* ---------- Devine l'usage et la hauteur voulue depuis la fiche ---------- */
function usageFig(f){
  const t = (f.taille||"").toLowerCase();
  if(/porte|clé|cle|aimant|jeu|pion/.test(t)) return "manipule";
  if(f.usage === "vente") return "figurine_vente";
  return "figurine_vente";
}
function hauteurFig(f){
  const t = (f.taille||"");
  let m = t.match(/(\d+[.,]?\d*)\s*cm/i);
  if(m) return Math.round(parseFloat(m[1].replace(",","."))*10);
  m = t.match(/(\d+[.,]?\d*)\s*mm/i);
  if(m) return Math.round(parseFloat(m[1].replace(",",".")));
  if(/porte|clé|cle|aimant/.test(t.toLowerCase())) return 55;
  return 100; // défaut : 10 cm
}

/* ---------- La recette : réglages à partir de usage + taille + matière ---------- */
function recette(usageKey, dims, matKey, opt){
  opt = opt || {};
  const u = USAGES[usageKey] || USAGES.figurine_vente;
  const mat = MATIERES[matKey] || MATIERES.PLA;
  const buseT = (opt.buse != null && opt.buse !== "") ? parseInt(opt.buse) : mat.buse;
  const plateauT = (opt.plateau != null && opt.plateau !== "") ? parseInt(opt.plateau) : mat.plateau;
  const alertes = [];
  const imp = imprimanteActuelle();
  const plate = [imp.x, imp.y, imp.z];
  const trop = ["x","y","z"].filter((a,i)=>[dims.x,dims.y,dims.z][i] > plate[i]-2);
  if(mat.enceinte && !imp.enceinte) alertes.push({n:"bad",t:mat.label+" a besoin d'une imprimante à caisson fermé, or "+imp.label+" n'en a pas : ça risque de décoller/gondoler. Prends plutôt du PLA ou du PETG."});
  const plusPetit = Math.min(dims.x,dims.y,dims.z);
  if(plusPetit < 30) alertes.push({n:"info",t:"Objet petit ("+Math.round(plusPetit)+" mm) : les petits détails passent mieux à partir de ~8 cm."});
  // élancé -> bordure ; porte-clés à plat -> pas de supports
  const aPlat = usageKey==="manipule";
  const elance = dims.z / Math.max(1, Math.min(dims.x,dims.y));
  const supports = !aPlat;
  const bordure = !aPlat && (elance>=3 || mat.enceinte);
  const bambu = {
    layer_height:String(u.couche), initial_layer_print_height:"0.2",
    sparse_infill_density:u.dens+"%", sparse_infill_pattern:u.motif,
    wall_loops:String(u.murs), top_shell_layers:"4", bottom_shell_layers:"4",
    nozzle_temperature:[String(buseT)], nozzle_temperature_initial_layer:[String(buseT)],
    hot_plate_temp:[String(plateauT)], hot_plate_temp_initial_layer:[String(plateauT)],
    fan_max_speed:[String(mat.ventilo)], fan_min_speed:[String(Math.round(mat.ventilo*0.6))],
    enable_support: supports?"1":"0", support_type:"tree(auto)", support_threshold_angle:"30",
    brim_type: bordure?"outer_only":"no_brim", brim_width: bordure?"5":"0",
    outer_wall_speed:String(mat.vpar), initial_layer_speed:"20",
    retraction_length:[String(mat.retr)], filament_type:[mat.label.split(" ")[0]],
    printer_model:"Bambu Lab P2S", printer_settings_id:"Bambu Lab P2S 0.4 nozzle",
    nozzle_diameter:["0.4"], printable_area:["0x0","256x0","256x256","0x256"], printable_height:"256",
    version:"01.09.00.00", from:"Atelier Figurines 3D"
  };
  const reglages = {
    usage:u.label, matiere:mat.label, couche:u.couche, dens:u.dens, motif:u.motifFr,
    buse:buseT, plateau:plateauT, supports, bordure, ventilo:mat.ventilo,
    murs:u.murs, vpar:mat.vpar, retr:mat.retr
  };
  let resume = u.label+" en "+mat.label+" : couche "+u.couche+" mm, remplissage "+u.dens+" % "+u.motifFr
    +", buse "+buseT+"°C / plateau "+plateauT+"°C"+(supports?", supports auto":"")+(bordure?", bordure d'accroche":"")+".";
  if(trop.length) resume += " L'objet dépasse le plateau : il sera coupé en morceaux.";
  return { reglages, bambu, alertes, decoupe:{requise:trop.length>0, axes:trop}, resume, ok:!alertes.some(a=>a.n==="bad") };
}

/* ---------- Fabrique le fichier .3mf (le fichier que Bambu ouvre) ---------- */
async function faire3mf(mesh, bambu, nom){
  const fflate = await import("https://esm.sh/fflate@0.8.2");
  const enc = s => new TextEncoder().encode(s);
  const V = mesh.vertices, T = mesh.triangles;
  let vx = ""; for(let i=0;i<V.length;i++) vx += `    <vertex x="${(+V[i][0]).toFixed(4)}" y="${(+V[i][1]).toFixed(4)}" z="${(+V[i][2]).toFixed(4)}"/>\n`;
  let tx = ""; for(let i=0;i<T.length;i++) tx += `    <triangle v1="${T[i][0]}" v2="${T[i][1]}" v3="${T[i][2]}"/>\n`;
  const model = `<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <metadata name="Title">${esc(nom)}</metadata>
 <resources><object id="1" type="model"><mesh>
  <vertices>
${vx}  </vertices>
  <triangles>
${tx}  </triangles>
 </mesh></object></resources>
 <build><item objectid="1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/></build>
</model>`;
  const ct = `<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="config" ContentType="application/vnd.ms-printing.printticket+xml"/>
</Types>`;
  const rels = `<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>`;
  const files = {
    "[Content_Types].xml": enc(ct),
    "_rels/.rels": enc(rels),
    "3D/3dmodel.model": enc(model),
    "Metadata/project_settings.config": enc(JSON.stringify(bambu, null, 1))
  };
  return fflate.zipSync(files, { level: 6 });
}

/* ---------- Charge la 3D (.glb) et la sort en millimètres, debout ---------- */
async function chargerMeshMM(url, hauteurMM){
  const THREE = await import("https://esm.sh/three@0.160.0");
  const { GLTFLoader } = await import("https://esm.sh/three@0.160.0/examples/jsm/loaders/GLTFLoader.js");
  const loader = new GLTFLoader();
  const gltf = await new Promise((res, rej) => loader.load(url, res, undefined, rej));
  // rassemble tous les morceaux en une seule liste de triangles
  const tris = [];
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse(o => {
    if(o.isMesh && o.geometry){
      const g = o.geometry.index ? o.geometry.toNonIndexed() : o.geometry;
      const pos = g.attributes.position; const m = o.matrixWorld;
      const v = new THREE.Vector3();
      for(let i=0;i<pos.count;i+=3){
        const p=[];
        for(let k=0;k<3;k++){ v.fromBufferAttribute(pos, i+k).applyMatrix4(m); p.push([v.x,v.y,v.z]); }
        tris.push(p);
      }
    }
  });
  if(!tris.length) throw new Error("modèle 3D vide");
  // Y en haut (glb) -> Z en haut (impression) : (x,y,z) -> (x,-z,y)
  for(const t of tris) for(const p of t){ const y=p[1],z=p[2]; p[1]=-z; p[2]=y; }
  // taille : met la hauteur (Z) à hauteurMM
  let mn=[1e9,1e9,1e9], mx=[-1e9,-1e9,-1e9];
  for(const t of tris) for(const p of t) for(let k=0;k<3;k++){ mn[k]=Math.min(mn[k],p[k]); mx[k]=Math.max(mx[k],p[k]); }
  const hz = mx[2]-mn[2] || 1; const s = hauteurMM/hz;
  for(const t of tris) for(const p of t) for(let k=0;k<3;k++){ p[k]=(p[k]-mn[k])*s; }
  // reconstruit dims + format {vertices, triangles}
  const vertices=[], triangles=[]; let dmx=[-1e9,-1e9,-1e9];
  for(const t of tris){ const idx=[]; for(const p of t){ idx.push(vertices.length); vertices.push(p); for(let k=0;k<3;k++) dmx[k]=Math.max(dmx[k],p[k]); } triangles.push(idx); }
  return { mesh:{vertices,triangles}, THREE, dims:{x:dmx[0],y:dmx[1],z:dmx[2]} };
}

/* ---------- Découpe le grand objet en morceaux qui s'emboîtent ---------- */
async function decouper(THREE, mesh, dims){
  // charge les outils de découpe (opérations booléennes 3D)
  const bvh = await import("https://esm.sh/three-mesh-bvh@0.7.0?deps=three@0.160.0");
  const csg = await import("https://esm.sh/three-bvh-csg@0.0.16?deps=three@0.160.0");
  const { Brush, Evaluator, ADDITION, SUBTRACTION } = csg;
  const imp = imprimanteActuelle();
  const plate = [imp.x, imp.y, imp.z];
  const utileAxe = a => plate[a] - MARGE;

  function toGeom(m){
    const g = new THREE.BufferGeometry();
    const arr = new Float32Array(m.triangles.length*9);
    let o=0; for(const t of m.triangles) for(const idx of t){ const p=m.vertices[idx]; arr[o++]=p[0];arr[o++]=p[1];arr[o++]=p[2]; }
    g.setAttribute("position", new THREE.BufferAttribute(arr,3)); g.computeVertexNormals(); return g;
  }
  function toMesh(geom){
    geom = geom.index ? geom.toNonIndexed() : geom;
    const pos=geom.attributes.position, vertices=[], triangles=[];
    for(let i=0;i<pos.count;i+=3){ const idx=[]; for(let k=0;k<3;k++){ idx.push(vertices.length); vertices.push([pos.getX(i+k),pos.getY(i+k),pos.getZ(i+k)]); } triangles.push(idx); }
    return {vertices,triangles};
  }
  function bbox(geom){ geom.computeBoundingBox(); const b=geom.boundingBox; return {min:b.min,max:b.max,sz:new THREE.Vector3().subVectors(b.max,b.min)}; }

  const ev = new Evaluator();
  let geoms = [toGeom(mesh)];
  const joints = []; let garde=0;
  while(garde++ < 20){
    let gi=-1, axe=-1;
    for(let i=0;i<geoms.length;i++){ const s=bbox(geoms[i]).sz; const c=[s.x,s.y,s.z]; for(let a=0;a<3;a++) if(c[a]>utileAxe(a)){ gi=i;axe=a;break;} if(gi>=0)break; }
    if(gi<0) break;
    const g = geoms.splice(gi,1)[0]; const bb=bbox(g);
    // coupe au milieu de la zone imprimable (assez robuste)
    const lo=[bb.min.x,bb.min.y,bb.min.z][axe], hi=[bb.max.x,bb.max.y,bb.max.z][axe];
    let cut = lo + Math.min(utileAxe(axe)-1, (hi-lo)/2);
    const centre = new THREE.Vector3((bb.min.x+bb.max.x)/2,(bb.min.y+bb.max.y)/2,(bb.min.z+bb.max.z)/2);
    // deux gros pavés pour couper de part et d'autre
    const grand = Math.max(bb.sz.x,bb.sz.y,bb.sz.z)*2 + 50;
    function pave(dep){ const b=new THREE.BoxGeometry(grand,grand,grand); const c=centre.clone(); const off=grand/2*dep; if(axe===0)c.x=cut+off; if(axe===1)c.y=cut+off; if(axe===2)c.z=cut+off; b.translate(c.x,c.y,c.z); return new Brush(b); }
    const src = new Brush(g);
    let bas = ev.evaluate(src, pave(-1), SUBTRACTION);   // garde côté "haut" du plan (enlève le pavé du bas)
    let haut = ev.evaluate(src, pave(1), SUBTRACTION);   // garde côté "bas"
    // ergots : un cylindre au centre, mâle sur "bas", femelle (trou) sur "haut"
    try {
      const R=2.5, sortie=5, ancr=4, jeu=0.2;
      const cyl = (r,h,shift)=>{ const cg=new THREE.CylinderGeometry(r,r,h,24); if(axe===0)cg.rotateZ(Math.PI/2); if(axe===2)cg.rotateX(Math.PI/2); const c=centre.clone(); if(axe===0)c.x=cut+shift; if(axe===1)c.y=cut+shift; if(axe===2)c.z=cut+shift; cg.translate(c.x,c.y,c.z); return new Brush(cg); };
      const male = cyl(R, ancr+sortie, (sortie-ancr)/2);
      const fem  = cyl(R+jeu, sortie+jeu+1, (sortie+jeu+1)/2-0.5);
      bas = ev.evaluate(bas, male, ADDITION);
      haut = ev.evaluate(haut, fem, SUBTRACTION);
      joints.push({axe:["X","Y","Z"][axe], goujons:1});
    } catch(e){ joints.push({axe:["X","Y","Z"][axe], goujons:0, note:"coupe simple (ergot non posé)"}); }
    geoms.push(bas, haut);
  }
  return { pieces: geoms.map(toMesh), joints };
}

/* ---------- Export STL (format universel, sans réglages, pour autres logiciels) ---------- */
function stlBinaire(mesh){
  const V=mesh.vertices, T=mesh.triangles;
  const buf=new ArrayBuffer(84 + T.length*50);
  const dv=new DataView(buf);
  dv.setUint32(80, T.length, true);
  let o=84;
  for(const t of T){
    const a=V[t[0]], b=V[t[1]], c=V[t[2]];
    const ux=b[0]-a[0], uy=b[1]-a[1], uz=b[2]-a[2];
    const vx=c[0]-a[0], vy=c[1]-a[1], vz=c[2]-a[2];
    let nx=uy*vz-uz*vy, ny=uz*vx-ux*vz, nz=ux*vy-uy*vx;
    const len=Math.hypot(nx,ny,nz)||1; nx/=len; ny/=len; nz/=len;
    dv.setFloat32(o,nx,true);dv.setFloat32(o+4,ny,true);dv.setFloat32(o+8,nz,true);o+=12;
    for(const p of [a,b,c]){ dv.setFloat32(o,+p[0],true);dv.setFloat32(o+4,+p[1],true);dv.setFloat32(o+8,+p[2],true);o+=12; }
    dv.setUint16(o,0,true);o+=2;
  }
  return new Uint8Array(buf);
}

/* ---------- Contrôle d'imprimabilité : mesure le VRAI fichier 3D ---------- */
function imprimabilite(mesh, dims){
  const V=mesh.vertices, T=mesh.triangles;
  // recolle les sommets par position arrondie (0,01 mm) pour analyser la surface
  const map=new Map();
  const idOf=p=>{ const k=Math.round(p[0]*100)+"_"+Math.round(p[1]*100)+"_"+Math.round(p[2]*100); let id=map.get(k); if(id===undefined){ id=map.size; map.set(k,id); } return id; };
  const edges=new Map(); let degen=0;
  for(const t of T){
    const ia=idOf(V[t[0]]), ib=idOf(V[t[1]]), ic=idOf(V[t[2]]);
    if(ia===ib||ib===ic||ia===ic){ degen++; continue; }
    for(const pr of [[ia,ib],[ib,ic],[ic,ia]]){ const e=pr[0]<pr[1]?pr[0]+"_"+pr[1]:pr[1]+"_"+pr[0]; edges.set(e,(edges.get(e)||0)+1); }
  }
  let bord=0, nonmani=0;
  for(const c of edges.values()){ if(c===1) bord++; else if(c>2) nonmani++; }
  const minDim=Math.min(dims.x,dims.y,dims.z);
  const solide = bord===0 && nonmani===0;
  const alertes=[];
  if(solide) alertes.push({n:"okk", t:"La sculpture est fermée (étanche) ✅ — prête à imprimer."});
  if(bord>0) alertes.push({n:"warn", t:"La surface a "+bord+" bord(s) ouvert(s) (petits trous). La plupart des logiciels d'impression les rebouchent seuls ; si une impression rate à un endroit, c'est souvent de là que ça vient."});
  if(nonmani>0) alertes.push({n:"warn", t:nonmani+" arête(s) où plusieurs faces se croisent. À surveiller — le logiciel d'impression corrige en général tout seul."});
  if(degen>0) alertes.push({n:"info", t:degen+" mini-facette(s) plate(s) ignorée(s) (sans conséquence)."});
  if(minDim<8) alertes.push({n:"bad", t:"La partie la plus fine fait ≈ "+minDim.toFixed(1)+" mm : c'est très fragile, ça risque de casser. Agrandis un peu si tu peux."});
  else if(minDim<15) alertes.push({n:"info", t:"Plus petite dimension ≈ "+minDim.toFixed(1)+" mm : imprimable, mais les petits détails ressortent mieux à partir de ~2-3 cm."});
  return { solide, bord, nonmani, degen, minDim, alertes };
}

/* ---------- Solidité : mesure la vraie épaisseur locale (épée, doigts…) ---------- */
async function mesureEpaisseurMM(THREE, mesh){
  const { MeshBVH, acceleratedRaycast } = await import("https://esm.sh/three-mesh-bvh@0.7.0?deps=three@0.160.0");
  THREE.Mesh.prototype.raycast = acceleratedRaycast;
  const V = mesh.vertices, T = mesh.triangles;
  const arr = new Float32Array(T.length*9);
  let o=0; for(const t of T) for(const idx of t){ const p=V[idx]; arr[o++]=p[0];arr[o++]=p[1];arr[o++]=p[2]; }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(arr,3));
  g.boundsTree = new MeshBVH(g);
  const mobj = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
  const rc = new THREE.Raycaster(); rc.firstHitOnly = true;
  const ep = [];
  const step = Math.max(1, Math.floor(T.length/1200));
  const va=new THREE.Vector3(), vb=new THREE.Vector3(), vc=new THREE.Vector3(), n=new THREE.Vector3(), cnt=new THREE.Vector3(), dir=new THREE.Vector3(), org=new THREE.Vector3();
  for(let i=0;i<T.length;i+=step){
    const a=V[T[i][0]], b=V[T[i][1]], c=V[T[i][2]];
    va.set(a[0],a[1],a[2]); vb.set(b[0],b[1],b[2]); vc.set(c[0],c[1],c[2]);
    cnt.set((a[0]+b[0]+c[0])/3, (a[1]+b[1]+c[1])/3, (a[2]+b[2]+c[2])/3);
    n.copy(vb).sub(va).cross(vc.sub(va));
    if(n.lengthSq() < 1e-12) continue;
    n.normalize();
    dir.copy(n).negate();
    org.copy(cnt).addScaledVector(dir, 0.05);
    rc.set(org, dir);
    const hit = rc.intersectObject(mobj, false)[0];
    if(hit && hit.distance > 0.01 && hit.distance < 500) ep.push(hit.distance + 0.05);
  }
  if(ep.length < 30) return null;
  ep.sort((x,y)=>x-y);
  const q = p => ep[Math.min(ep.length-1, Math.floor(p*ep.length))];
  return { p5: q(0.05), med: q(0.5), n: ep.length };
}

/* ---------- Bouton principal : crée le(s) fichier(s) .3mf ---------- */
window.creerImpression = async function(i){
  const f = FIGS[i]; const log = $("impr-log"); const btn = $("impr-go");
  if(!f || !f.model_url){ log.textContent = "La 3D n'est pas encore prête pour cette figurine."; return; }
  const matKey = ($("impr-mat")||{}).value || localStorage.getItem('atelier_matiere') || "PLA";
  const hauteur = parseFloat(($("impr-haut")||{}).value) || hauteurFig(f);
  const usageKey = ($("impr-usage")||{}).value || usageFig(f);
  const tempOpt = { buse: parseInt(($("impr-buse")||{}).value)||undefined, plateau: parseInt(($("impr-plateau")||{}).value)||undefined };
  btn.textContent = "⏳ Préparation…"; btn.style.pointerEvents="none";
  log.textContent = "Je récupère ta figurine en 3D…";
  try {
    const { mesh, THREE, dims } = await chargerMeshMM(f.model_url, hauteur);
    log.textContent = "Je vérifie que la sculpture est bien imprimable…";
    const diag = imprimabilite(mesh, dims);
    try {
      log.textContent = "Je mesure la solidité (épaisseur des parties fines : épée, doigts…)…";
      const th = await mesureEpaisseurMM(THREE, mesh);
      if(th){
        if(th.p5 < 1.5) diag.alertes.push({n:"bad", t:"Solidité : des parties très fines (≈ "+th.p5.toFixed(1)+" mm — épée, doigts, accessoires…) risquent de CASSER. Conseil : agrandis la figurine ou demande dans le chat d'épaissir/renforcer cet élément avant d'imprimer."});
        else if(th.p5 < 3) diag.alertes.push({n:"warn", t:"Solidité : les parties les plus fines font ≈ "+th.p5.toFixed(1)+" mm. Imprimable, mais fragile à manipuler — pour du costaud, agrandis un peu."});
        else diag.alertes.push({n:"okk", t:"Solidité : parties les plus fines ≈ "+th.p5.toFixed(1)+" mm — bonne tenue. ✅"});
      }
    } catch(e){}
    let diagHtml = `<div class="impr" style="margin-top:8px"><div class="l">🔍 Contrôle d'imprimabilité et de solidité (mesuré sur le vrai fichier 3D)</div>`;
    for(const a of diag.alertes) diagHtml += `<div class="al ${a.n}">${esc(a.t)}</div>`;
    diagHtml += `</div>`;
    $("impr-dl").innerHTML = diagHtml;
    const rec = recette(usageKey, dims, matKey, tempOpt);
    let sorties = [];
    if(!rec.decoupe.requise){
      log.textContent = "Je prépare le fichier avec les bons réglages…";
      const zip = await faire3mf(mesh, rec.bambu, "figurine_"+f.id);
      sorties.push({nom:"figurine_"+f.id+"_a_imprimer.3mf", data:zip});
      sorties.push({nom:"figurine_"+f.id+".stl", data:stlBinaire(mesh)});
    } else {
      log.textContent = "Objet trop grand : je le coupe en morceaux qui s'emboîtent… (ça peut prendre 10-30 s)";
      const { pieces, joints } = await decouper(THREE, mesh, dims);
      for(let p=0;p<pieces.length;p++){
        // recalcule dims de la pièce
        let mx=[-1e9,-1e9,-1e9], mn=[1e9,1e9,1e9];
        for(const v of pieces[p].vertices) for(let k=0;k<3;k++){ mx[k]=Math.max(mx[k],v[k]); mn[k]=Math.min(mn[k],v[k]); }
        const dp={x:mx[0]-mn[0],y:mx[1]-mn[1],z:mx[2]-mn[2]};
        const rp = recette(usageKey, dp, matKey, tempOpt);
        const zip = await faire3mf(pieces[p], rp.bambu, "figurine_"+f.id+"_piece"+(p+1));
        sorties.push({nom:"figurine_"+f.id+"_piece"+(p+1)+".3mf", data:zip});
        sorties.push({nom:"figurine_"+f.id+"_piece"+(p+1)+".stl", data:stlBinaire(pieces[p])});
      }
      log.textContent = "Coupé en "+pieces.length+" morceaux. Imprime-les, emboîte les ergots, colle. ✅";
    }
    // liens de téléchargement
    let html = "";
    for(const s of sorties){
      const url = URL.createObjectURL(new Blob([s.data], {type:"application/octet-stream"}));
      const est3mf = s.nom.endsWith(".3mf");
      const lab = est3mf ? ("📥 "+esc(s.nom)+" — prêt à imprimer (réglages inclus)") : ("📄 "+esc(s.nom)+" — format universel, autres logiciels");
      html += `<a class="abtn ${est3mf?'vert':'sec'}" href="${url}" download="${s.nom}" style="margin-top:8px">${lab}</a>`;
    }
    $("impr-dl").innerHTML = diagHtml + html;
    btn.textContent = "🔄 Refaire le fichier"; btn.style.pointerEvents="auto";
  } catch(e){
    log.textContent = "Souci pendant la préparation : "+(e.message||e)+"\nDis-le à Franck, il a une version de secours qui marche à coup sûr.";
    btn.textContent = "🔁 Réessayer"; btn.style.pointerEvents="auto";
  }
};

/* ---------- Changement d'imprimante (recalcule tout selon la machine) ---------- */
window.majImprimante = function(k, i){ localStorage.setItem('atelier_imprimante', k); renderImpr(i); };
window.majMatiere = function(v, i){ localStorage.setItem('atelier_matiere', v); renderImpr(i); };
window.majUsage = function(v, i){ const f=FIGS[i]; if(f) localStorage.setItem('atelier_usage_'+f.id, v); renderImpr(i); };
window.majHauteur = function(v, i){ const f=FIGS[i]; if(f) localStorage.setItem('atelier_haut_'+f.id, v); renderImpr(i); };
window.majMarque = function(v, i){ const m=localStorage.getItem('atelier_matiere')||'PLA'; localStorage.setItem('atelier_marque_'+m, v); localStorage.removeItem('atelier_buse_'+m+'_'+v); localStorage.removeItem('atelier_plateau_'+m+'_'+v); renderImpr(i); };
window.majTemp = function(which, v, i){ const m=localStorage.getItem('atelier_matiere')||'PLA'; const mq=localStorage.getItem('atelier_marque_'+m)||'generique'; localStorage.setItem('atelier_'+which+'_'+m+'_'+mq, v); renderImpr(i); };

/* ---------- Affiche le panneau impression dans la fiche ---------- */
function renderImpr(i){
  const f = FIGS[i]; const el = $("impr-panel"); if(!el) return;
  if(!f.model_url){
    el.innerHTML = `<div class="impr"><div class="l">🖨️ Fichier d'impression</div><div class="rz">La 3D n'est pas encore prête. Valide d'abord la sculpture, puis reviens ici.</div></div>`;
    return;
  }
  const matKey = localStorage.getItem('atelier_matiere') || 'PLA';
  const usageKey = localStorage.getItem('atelier_usage_'+f.id) || usageFig(f);
  const haut = parseFloat(localStorage.getItem('atelier_haut_'+f.id)) || hauteurFig(f);
  const marque = localStorage.getItem('atelier_marque_'+matKey) || 'generique';
  const fdef = (FILAMENTS[matKey] && FILAMENTS[matKey][marque]) || {buse:(MATIERES[matKey]||MATIERES.PLA).buse, plateau:(MATIERES[matKey]||MATIERES.PLA).plateau};
  const buseT = parseInt(localStorage.getItem('atelier_buse_'+matKey+'_'+marque)) || fdef.buse;
  const plateauT = parseInt(localStorage.getItem('atelier_plateau_'+matKey+'_'+marque)) || fdef.plateau;
  const rec = recette(usageKey, {x:60,y:60,z:haut}, matKey, {buse:buseT, plateau:plateauT}); // aperçu (dims réelles à la génération)
  const optMat = Object.keys(MATIERES).map(k=>`<option value="${k}" ${k===matKey?"selected":""}>${MATIERES[k].label}</option>`).join("");
  const optUsage = Object.keys(USAGES).map(k=>`<option value="${k}" ${k===usageKey?"selected":""}>${USAGES[k].label}</option>`).join("");
  const curImp = localStorage.getItem('atelier_imprimante') || 'p2s';
  const optImp = Object.keys(IMPRIMANTES).map(k=>`<option value="${k}" ${k===curImp?"selected":""}>${IMPRIMANTES[k].label}</option>`).join("");
  const optMarque = Object.keys(FILAMENTS[matKey]||{generique:1}).map(k=>`<option value="${k}" ${k===marque?"selected":""}>${FILAMENT_LABELS[k]||k}</option>`).join("");
  let al = "";
  for(const a of rec.alertes) al += `<div class="al ${a.n}">${esc(a.t)}</div>`;
  el.innerHTML = `<div class="impr">
    <div class="l">🖨️ Fichier d'impression (l'appli règle tout toute seule)</div>
    <div class="rz">${esc(rec.resume)}</div>
    ${al}
    <div id="impr-dl"></div>
    <button class="abtn" id="impr-go" onclick="creerImpression(${i})" style="margin-top:10px">📥 Créer le fichier à imprimer (.3mf)</button>
    <div class="imprlog" id="impr-log"></div>
    <details class="tech">
      <summary>🔧 Réglages détaillés (si tu veux voir ou changer)</summary>
      <div style="font-size:12.5px;color:#9aa0a6;margin-top:6px">Tout est automatique. Ici tu peux changer le plastique, la taille et l'usage. Si tu t'éloignes du conseil, tu restes maître.</div>
      <table class="techtab">
        <tr><td>Ton imprimante</td><td><select id="impr-machine" onchange="majImprimante(this.value, ${i})">${optImp}</select></td></tr>
        <tr><td>Quel plastique as-tu ?</td><td><select id="impr-mat" onchange="majMatiere(this.value, ${i})">${optMat}</select></td></tr>
        <tr><td>Marque du filament</td><td><select id="impr-marque" onchange="majMarque(this.value, ${i})">${optMarque}</select></td></tr>
        <tr><td>Usage</td><td><select id="impr-usage" onchange="majUsage(this.value, ${i})">${optUsage}</select></td></tr>
        <tr><td>Hauteur voulue (mm)</td><td><input id="impr-haut" type="number" value="${haut}" min="10" onchange="majHauteur(this.value, ${i})"></td></tr>
        <tr><td>Température buse (°C)</td><td><input id="impr-buse" type="number" value="${buseT}" onchange="majTemp('buse', this.value, ${i})"></td></tr>
        <tr><td>Température plateau (°C)</td><td><input id="impr-plateau" type="number" value="${plateauT}" onchange="majTemp('plateau', this.value, ${i})"></td></tr>
        <tr><td>Couche (finesse)</td><td>${rec.reglages.couche} mm</td></tr>
        <tr><td>Remplissage</td><td>${rec.reglages.dens} % — ${rec.reglages.motif}</td></tr>
        <tr><td>Supports</td><td>${rec.reglages.supports?"oui (auto)":"non"}</td></tr>
        <tr><td>Bordure d'accroche</td><td>${rec.reglages.bordure?"oui":"non"}</td></tr>
      </table>
      <div style="font-size:12px;color:#9aa0a6;margin-top:6px">Astuce : ouvre le fichier .3mf dans Bambu Handy, vérifie que l'imprimante « Bambu Lab P2S » est bien choisie, puis lance.</div>
    </details>
  </div>`;
}

/* ============================================================= */
/*  TABLEAU PHOTO (LITHOPHANE) : photo -> plaque à imprimer      */
/* ============================================================= */
let LITHO = null; // { data:Float32Array(0..1), w, h }
(function(){
  const fileI = $("litho-file"); if(!fileI) return;
  fileI.addEventListener("change", e => {
    const f = e.target.files[0]; if(!f) return;
    const img = new Image();
    img.onload = () => {
      const maxW = 200;                       // résolution du relief
      const scale = Math.min(1, maxW/img.width);
      const w = Math.max(2, Math.round(img.width*scale));
      const h = Math.max(2, Math.round(img.height*scale));
      const cv = $("litho-prev"); cv.width = w; cv.height = h;
      const ctx = cv.getContext("2d"); ctx.drawImage(img, 0, 0, w, h);
      const d = ctx.getImageData(0,0,w,h).data;
      const data = new Float32Array(w*h);
      for(let i=0;i<w*h;i++){ data[i] = (0.299*d[i*4] + 0.587*d[i*4+1] + 0.114*d[i*4+2]) / 255; }
      LITHO = { data, w, h };
      cv.style.display = "block";
      $("litho-log").textContent = "Photo prête ("+w+"×"+h+" points). Clique sur « Générer ».";
      $("litho-dl").innerHTML = "";
      URL.revokeObjectURL(img.src);
    };
    img.onerror = () => { $("litho-log").textContent = "Cette image n'a pas pu être lue, réessaie avec une autre."; };
    img.src = URL.createObjectURL(f);
  });
})();

window.genererLithophane = async function(){
  const log = $("litho-log"), btn = $("litho-go");
  if(!LITHO){ log.textContent = "Choisis d'abord une photo (bouton au-dessus)."; return; }
  btn.textContent = "⏳ Génération…"; btn.style.pointerEvents = "none";
  log.textContent = "Je fabrique le relief de ta photo…";
  try {
    const larg = Math.max(20, parseFloat($("litho-larg").value)||100);
    let eMin = Math.max(0.4, parseFloat($("litho-min").value)||0.8);
    let eMax = Math.max(eMin+0.2, parseFloat($("litho-max").value)||3);
    const cadre = parseFloat($("litho-cadre").value)||0;
    const { data, w:W, h:H } = LITHO;
    const px = larg / W;                 // mm par point
    const hAt = (x,y) => eMin + (1 - data[y*W + x]) * (eMax - eMin);   // sombre = épais
    const vertices = [], triangles = [];
    const topIdx = new Int32Array(W*H), botIdx = new Int32Array(W*H);
    // sommets face avant (relief) — X inversé pour que l'image se lise du bon côté
    for(let y=0;y<H;y++) for(let x=0;x<W;x++){ topIdx[y*W+x]=vertices.length; vertices.push([(W-1-x)*px,(H-1-y)*px,hAt(x,y)]); }
    // sommets face arrière (plate, z=0)
    for(let y=0;y<H;y++) for(let x=0;x<W;x++){ botIdx[y*W+x]=vertices.length; vertices.push([(W-1-x)*px,(H-1-y)*px,0]); }
    // faces avant
    for(let y=0;y<H-1;y++) for(let x=0;x<W-1;x++){
      const a=topIdx[y*W+x], b=topIdx[y*W+x+1], c=topIdx[(y+1)*W+x+1], d=topIdx[(y+1)*W+x];
      triangles.push([a,b,c]); triangles.push([a,c,d]);
    }
    // faces arrière (sens inversé)
    for(let y=0;y<H-1;y++) for(let x=0;x<W-1;x++){
      const a=botIdx[y*W+x], b=botIdx[y*W+x+1], c=botIdx[(y+1)*W+x+1], d=botIdx[(y+1)*W+x];
      triangles.push([a,c,b]); triangles.push([a,d,c]);
    }
    // murs sur les 4 bords (relie l'avant et l'arrière -> plaque fermée)
    const mur = seq => { for(let i=0;i<seq.length-1;i++){
      const p=seq[i], q=seq[i+1];
      const t0=topIdx[p[1]*W+p[0]], t1=topIdx[q[1]*W+q[0]], b0=botIdx[p[1]*W+p[0]], b1=botIdx[q[1]*W+q[0]];
      triangles.push([t0,t1,b1]); triangles.push([t0,b1,b0]);
    } };
    const hb=[], bb=[], lb=[], rb=[];
    for(let x=0;x<W;x++){ hb.push([x,0]); bb.push([x,H-1]); }
    for(let y=0;y<H;y++){ lb.push([0,y]); rb.push([W-1,y]); }
    mur(hb); mur(rb); mur(bb); mur(lb);
    const mesh = { vertices, triangles };
    // dimensions réelles
    const dims = { x: larg, y: px*H, z: eMax + cadre*0 };
    // réglages : PLA, couche fine, 100% de remplissage (bloque bien la lumière), à plat, sans support
    const rec = recette('figurine_vente', {x:dims.x,y:dims.y,z:dims.z}, 'PLA', {});
    const bambu = Object.assign({}, rec.bambu, {
      layer_height:"0.08", sparse_infill_density:"100%", sparse_infill_pattern:"rectilinear",
      enable_support:"0", brim_type:(cadre>0?"no_brim":"outer_only"), brim_width:(cadre>0?"0":"3"),
      top_shell_layers:"5", bottom_shell_layers:"3", from:"Atelier Figurines 3D - Tableau photo"
    });
    log.textContent = "Je prépare les fichiers…";
    const nom = "tableau_photo";
    const zip = await faire3mf(mesh, bambu, nom);
    const sorties = [ {nom:nom+"_a_imprimer.3mf", data:zip}, {nom:nom+".stl", data:stlBinaire(mesh)} ];
    let html = `<div class="impr" style="margin-top:8px"><div class="l">✅ Ton tableau est prêt — ${W}×${H} points, ${larg.toFixed(0)}×${(px*H).toFixed(0)} mm, ${eMin}→${eMax} mm d'épaisseur</div></div>`;
    for(const s of sorties){
      const url = URL.createObjectURL(new Blob([s.data], {type:"application/octet-stream"}));
      const est3mf = s.nom.endsWith(".3mf");
      const lab = est3mf ? ("📥 "+s.nom+" — prêt à imprimer (réglages inclus)") : ("📄 "+s.nom+" — format universel");
      html += `<a class="abtn ${est3mf?'vert':'sec'}" href="${url}" download="${s.nom}" style="margin-top:8px">${lab}</a>`;
    }
    $("litho-dl").innerHTML = html;
    log.textContent = "Terminé ! Imprime à plat, en blanc, couche 0,08 mm, 100% de remplissage. 🖼️";
    btn.textContent = "🔄 Refaire le fichier"; btn.style.pointerEvents = "auto";
  } catch(e){
    log.textContent = "Souci pendant la génération : "+(e.message||e);
    btn.textContent = "🔁 Réessayer"; btn.style.pointerEvents = "auto";
  }
};

/* ============================================================= */
/*  CATALOGUE DES CRÉATIONS (catégories + moteur de recherche)  */
/* ============================================================= */
const CATALOGUE = [
  // Déco
  {nom:"Figurine / statuette déco", cat:"Déco", emoji:"🗿", desc:"Un personnage ou un objet à poser sur une étagère.", tag:"8 à 18 cm", prompt:"Je voudrais une statuette déco de "},
  {nom:"Buste", cat:"Déco", emoji:"🗿", desc:"La tête et les épaules d'un personnage, effet sculpture.", tag:"déco", prompt:"Je voudrais un buste de "},
  {nom:"Bas-relief mural", cat:"Déco", emoji:"🖼️", desc:"Une scène en relief peu épaisse à accrocher au mur.", tag:"mural", prompt:"Je voudrais un bas-relief mural représentant "},
  {nom:"Vase / cache-pot déco", cat:"Déco", emoji:"🏺", desc:"Un vase décoratif (pour fleurs séchées ou déco).", tag:"déco", prompt:"Je voudrais un vase déco style "},
  {nom:"Socle / présentoir", cat:"Déco", emoji:"🧱", desc:"Un support pour mettre en valeur un objet ou une figurine.", tag:"support", prompt:"Je voudrais un petit socle présentoir pour "},
  // Cadeau / perso
  {nom:"Figurine personnalisée (d'après photo)", cat:"Cadeau", emoji:"🧍", desc:"Une figurine à ton effigie ou celle d'un proche, à partir de photos.", tag:"perso", prompt:"Je voudrais une figurine d'après cette photo : "},
  {nom:"Médaillon photo", cat:"Cadeau", emoji:"📿", desc:"Un petit médaillon rond avec un visage ou un motif en relief.", tag:"cadeau", prompt:"Je voudrais un médaillon avec "},
  {nom:"Porte-clés", cat:"Cadeau", emoji:"🔑", desc:"Un petit objet avec la boucle d'accroche intégrée (anneau non fourni).", tag:"perso/vente", prompt:"Je voudrais un porte-clés en forme de "},
  {nom:"Aimant déco", cat:"Cadeau", emoji:"🧲", desc:"Un objet plat à coller sur le frigo (on colle un aimant acheté derrière).", tag:"cadeau", prompt:"Je voudrais un aimant déco en forme de "},
  {nom:"Marque-place / prénom", cat:"Cadeau", emoji:"🔤", desc:"Un prénom ou un mot en relief, pour la table ou la déco.", tag:"événement", prompt:"Je voudrais un marque-place avec le prénom "},
  // Utile
  {nom:"Support téléphone", cat:"Utile", emoji:"📱", desc:"Un socle pour poser le téléphone sur le bureau.", tag:"utile", prompt:"Je voudrais un support téléphone style "},
  {nom:"Vide-poche / range-bijoux", cat:"Utile", emoji:"🪙", desc:"Une petite coupelle pour clés, pièces ou bijoux.", tag:"utile", prompt:"Je voudrais un vide-poche en forme de "},
  {nom:"Dessous-de-verre", cat:"Utile", emoji:"🥃", desc:"Un sous-verre décoré, seul ou par lot.", tag:"utile", prompt:"Je voudrais un dessous-de-verre avec le motif "},
  {nom:"Crochet / patère murale", cat:"Utile", emoji:"🪝", desc:"Un crochet décoratif à visser au mur.", tag:"utile", prompt:"Je voudrais un crochet mural en forme de "},
  {nom:"Cache-câble / serre-câble", cat:"Utile", emoji:"🔌", desc:"Un petit clip pour ranger les câbles du bureau.", tag:"utile", prompt:"Je voudrais un range-câble en forme de "},
  // Photo
  {nom:"Tableau photo (lithophane)", cat:"Photo", emoji:"🖼️", desc:"Une plaque qui révèle une photo devant la lumière. Outil dédié dans l'app.", tag:"photo", litho:true},
  {nom:"Veilleuse photo", cat:"Photo", emoji:"💡", desc:"Un tableau photo courbé posé sur une LED : la photo s'illumine.", tag:"photo", prompt:"Je voudrais une veilleuse photo à partir de "},
  // Jeu
  {nom:"Figurine / pion de jeu", cat:"Jeu", emoji:"♟️", desc:"Un pion ou une figurine pour jeu de plateau ou de rôle.", tag:"jeu", prompt:"Je voudrais une figurine de jeu représentant "},
  {nom:"Dé personnalisé", cat:"Jeu", emoji:"🎲", desc:"Un dé avec des faces au choix.", tag:"jeu", prompt:"Je voudrais un dé personnalisé avec "},
  {nom:"Jeton / marqueur", cat:"Jeu", emoji:"🪙", desc:"Des jetons ou marqueurs pour un jeu.", tag:"jeu", prompt:"Je voudrais des jetons de jeu style "}
];
const CAT_CATS = ["Tout","Déco","Cadeau","Utile","Photo","Jeu"];
let catFiltre = "Tout";
function renderCat(){
  const box = $("cat-list"); if(!box) return;
  const q = ($("cat-search").value||"").toLowerCase().trim();
  const chip = (c,on) => `<button onclick="filtreCat('${c}')" style="background:${on?'#2563eb':'#2a2f3a'};color:${on?'#fff':'#dbe4ff'};border:1px solid #39404e;border-radius:16px;padding:6px 12px;font-size:13px;cursor:pointer">${c}</button>`;
  $("cat-chips").innerHTML = CAT_CATS.map(c=>chip(c, c===catFiltre)).join("");
  const items = CATALOGUE.filter(it => (catFiltre==="Tout"||it.cat===catFiltre) && (!q || (it.nom+" "+it.desc).toLowerCase().includes(q)));
  box.innerHTML = items.length ? items.map(it=>`
    <div class="tile" style="margin-bottom:8px">
      <div style="display:flex;gap:11px;align-items:flex-start">
        <div style="font-size:26px;line-height:1">${it.emoji}</div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:700;font-size:15px">${esc(it.nom)}</div>
          <div style="font-size:13px;color:#cbd5e1;margin-top:3px">${esc(it.desc)}</div>
          ${it.tag?`<span class="badge" style="margin-top:6px">${esc(it.tag)}</span>`:''}
          ${it.litho
            ? `<button class="abtn sec" style="margin-top:8px" onclick="allerLitho()">🖼️ Ouvrir l'outil tableau photo</button>`
            : `<button class="abtn sec" style="margin-top:8px" onclick="utiliserIdee(this.dataset.p)" data-p="${esc(it.prompt||('Je voudrais '+it.nom))}">💬 Demander cette création</button>`}
        </div>
      </div>
    </div>`).join("") : `<div style="color:#6b7280;text-align:center;padding:24px">Rien trouvé — essaie un autre mot.</div>`;
}
window.filtreCat = c => { catFiltre = c; renderCat(); };
window.utiliserIdee = txt => { const nb=document.querySelector('nav button[data-p="chat"]'); if(nb) nb.click(); const inp=$("inp"); if(inp){ inp.value=txt; inp.focus(); } };
window.allerLitho = () => { const nb=document.querySelector('nav button[data-p="litho"]'); if(nb) nb.click(); };
if($("cat-search")){ $("cat-search").addEventListener("input", renderCat); renderCat(); }

/* ============================================================= */
/*  CALCUL DU PRIX (coût de revient + prix de vente conseillé)  */
/* ============================================================= */
function calcPrix(){
  const el = $("px-res"); if(!el) return;
  const g = id => parseFloat(($(id)||{}).value)||0;
  const poids=g("px-poids"), temps=g("px-temps"), bobine=g("px-bobine"), watt=g("px-watt"), kwh=g("px-kwh");
  const marge=g("px-marge")||3, plancher=g("px-plancher");
  const cMat = poids/1000*bobine;
  const cElec = (watt/1000)*(temps/60)*kwh;
  const usure = 0.05*(cMat+cElec) + 0.10;   // usure machine + petits consommables
  const cout = cMat + cElec + usure;
  const prix = Math.max(plancher, cout*marge);
  const eur = n => n.toLocaleString("fr-FR",{minimumFractionDigits:2,maximumFractionDigits:2})+" €";
  el.innerHTML = `<div class="l">Résultat</div>
    <table class="techtab">
      <tr><td>Matière (${poids} g)</td><td>${eur(cMat)}</td></tr>
      <tr><td>Électricité (${temps} min)</td><td>${eur(cElec)}</td></tr>
      <tr><td>Usure machine + consommables</td><td>${eur(usure)}</td></tr>
      <tr><td><b>Coût de revient</b></td><td><b>${eur(cout)}</b></td></tr>
      <tr><td>Prix de vente conseillé (×${marge})</td><td style="color:#5be3a5"><b>${eur(prix)}</b></td></tr>
      <tr><td>Bénéfice estimé</td><td>${eur(prix-cout)}</td></tr>
    </table>`;
}
["px-poids","px-temps","px-bobine","px-watt","px-kwh","px-marge","px-plancher"].forEach(id=>{ const e=$(id); if(e) e.addEventListener("input", calcPrix); });
if($("px-res")) calcPrix();

/* ---------- Remplissage du plateau : combien de pièces tiennent ---------- */
function calcPlateau(){
  const el = $("pl-res"); if(!el) return;
  const sel = $("pl-imp");
  const imp = (typeof IMPRIMANTES!=="undefined" && IMPRIMANTES[sel && sel.value]) || imprimanteActuelle();
  const g = id => parseFloat(($(id)||{}).value)||0;
  const w=g("pl-larg"), dpt=g("pl-prof"), m=g("pl-marge");
  if(w<=0 || dpt<=0){ el.innerHTML = `<div class="l">Résultat</div><div class="al info">Entre la taille d'une pièce.</div>`; return; }
  const cols = Math.max(0, Math.floor((imp.x + m)/(w + m)));
  const rows = Math.max(0, Math.floor((imp.y + m)/(dpt + m)));
  const total = cols*rows;
  const occ = total>0 ? Math.min(100, Math.round((total*w*dpt)/(imp.x*imp.y)*100)) : 0;
  let msg;
  if(total<=0) msg = `<div class="al bad">Une pièce de ${w}×${dpt} mm est trop grande pour le plateau ${esc(imp.label)} (${imp.x}×${imp.y} mm) : il faudra la découper.</div>`;
  else msg = `<div class="al okk">Sur le plateau ${esc(imp.label)} (${imp.x}×${imp.y} mm), tu peux en poser jusqu'à <b>${total}</b> (${cols} × ${rows}). Occupation ≈ ${occ} %.${total>1?" Il reste de la place — tu peux en ajouter pour rentabiliser l'impression, mais tu lances quand tu veux.":""}</div>`;
  el.innerHTML = `<div class="l">Résultat</div>${msg}`;
}
(function(){
  const sel = $("pl-imp"); if(!sel || typeof IMPRIMANTES==="undefined") return;
  const cur = localStorage.getItem("atelier_imprimante") || "p2s";
  sel.innerHTML = Object.keys(IMPRIMANTES).map(k=>`<option value="${k}" ${k===cur?"selected":""}>${esc(IMPRIMANTES[k].label)}</option>`).join("");
  ["pl-larg","pl-prof","pl-marge"].forEach(id=>{ const e=$(id); if(e) e.addEventListener("input", calcPlateau); });
  sel.addEventListener("change", calcPlateau);
  calcPlateau();
})();
/* ---------- Outils dans la fiche : prix + plateau, par figurine ---------- */
function calcOutilsFiche(){
  const g = id => parseFloat(($(id)||{}).value)||0;
  const sel = $("fpl-imp");
  if(sel && !sel.options.length){
    const cur = localStorage.getItem("atelier_imprimante") || "p2s";
    sel.innerHTML = Object.keys(IMPRIMANTES).map(k=>`<option value="${k}" ${k===cur?"selected":""}>${esc(IMPRIMANTES[k].label)}</option>`).join("");
  }
  const pel = $("fpx-res");
  if(pel){
    const poids=g("fpx-poids"), temps=g("fpx-temps"), bobine=g("fpx-bobine"), watt=g("fpx-watt"), kwh=g("fpx-kwh");
    const marge=g("fpx-marge")||3, plancher=g("fpx-plancher");
    const cMat=poids/1000*bobine, cElec=(watt/1000)*(temps/60)*kwh, usure=0.05*(cMat+cElec)+0.10;
    const cout=cMat+cElec+usure, prix=Math.max(plancher, cout*marge);
    const e=n=>n.toLocaleString("fr-FR",{minimumFractionDigits:2,maximumFractionDigits:2})+" €";
    pel.innerHTML = `<div class="l">💶 Prix conseillé</div><table class="techtab"><tr><td>Coût de revient</td><td><b>${e(cout)}</b></td></tr><tr><td>Prix de vente (×${marge})</td><td style="color:#5be3a5"><b>${e(prix)}</b></td></tr><tr><td>Bénéfice</td><td>${e(prix-cout)}</td></tr></table>`;
  }
  plateauRender();
}
/* ---------- Mon plateau : cumulatif, pièce par pièce ---------- */
let PLATEAU = [];
function plateauImp(){ const sel=$("fpl-imp"); return (typeof IMPRIMANTES!=="undefined" && IMPRIMANTES[sel && sel.value]) || imprimanteActuelle(); }
window.plateauAjout = function(w, d, nom){
  const g = id => parseFloat(($(id)||{}).value)||0;
  w = w || g("fpl-larg"); d = d || g("fpl-prof");
  if(w>0 && d>0) PLATEAU.push({ w, d, nom: nom || (Math.round(w)+"×"+Math.round(d)+" mm") });
  plateauRender();
};
window.plateauAjoutFig = function(i){
  const f = FIGS[i]; if(!f) return;
  const hmm = hauteurFig(f);
  const base = Math.max(25, Math.min(120, Math.round(hmm*0.45)));
  plateauAjout(base, base, "#"+f.id+" (~"+base+"×"+base+" mm)");
};
window.plateauVider = function(){ PLATEAU = []; plateauRender(); };
window.plateauRender = function(){
  const lel = $("fpl-res"); if(!lel) return;
  const imp = plateauImp(); const M = 5;
  const X = imp.x - 4, Y = imp.y - 4;
  let x=0, y=0, rowH=0, places=0, aire=0; const hors=[];
  PLATEAU.forEach(p=>{
    if(p.w>X || p.d>Y){ hors.push(p.nom); return; }
    if(x + p.w > X){ x = 0; y += rowH + M; rowH = 0; }
    if(y + p.d > Y){ hors.push(p.nom); return; }
    x += p.w + M; rowH = Math.max(rowH, p.d); places++; aire += p.w*p.d;
  });
  const occ = Math.min(100, Math.round(aire/(X*Y)*100));
  let h = `<div class="l">📐 Mon plateau — ${esc(imp.label)} (${imp.x}×${imp.y} mm)</div>`;
  if(!PLATEAU.length){
    h += `<div class="al info">Plateau vide. Ajoute des pièces avec les boutons ➕ : le remplissage se met à jour à chaque ajout.</div>`;
  } else {
    h += `<div class="al ${hors.length ? 'warn' : 'okk'}">${places} pièce(s) posée(s) — plateau rempli à ≈ <b>${occ} %</b>.${hors.length ? " ⚠️ Ne rentre(nt) plus : "+esc(hors.join(", "))+"." : " Il reste de la place — tu peux en ajouter, mais tu lances quand tu veux."}</div>`;
    h += `<div style="font-size:12.5px;color:#9aa0a6;margin-top:6px">${PLATEAU.map(p=>"• "+esc(p.nom)).join("<br>")}</div>`;
  }
  lel.innerHTML = h;
};


/* === MODULE COMPTES/VITRINE/TARIFS (ajout 18/07, interrupteurs OFF) === */
/* ============================================================================
   ATELIER FIGURINES 3D — MODULE COMPTES CLIENTS + VITRINE + TARIFS
   Préparé le 18/07/2026 (run autonome). À COLLER dans index.html, à la fin du
   <script> existant (il réutilise SUPA, KEY, esc, chargerMeshMM, mesureEpaisseurMM).

   IMPORTANT — INTERRUPTEURS DE SÉCURITÉ (rien ne change tant qu'ils sont false) :
     COMPTES_ACTIFS = false  -> pas de mur de connexion : l'app marche comme avant
                                (parfait pour le test de l'ami du 21/07).
     STRIPE_ACTIF   = false  -> l'onglet Tarifs s'affiche mais le bouton Payer
                                explique "bientôt" au lieu d'appeler Stripe.
   Quand tout est prêt (app déployée + migration CUTOVER lancée + compte Stripe),
   passer ces deux drapeaux à true et redéployer.

   ÉTAPES D'INTÉGRATION HTML (voir GUIDE_INTEGRATION.md) :
     1) Ajouter les 3 sections <section class="page" id="p-valid|p-tarifs|p-cgv">.
     2) Ajouter les boutons de nav correspondants.
     3) Remplacer, dans les fetch chat/figurines/avis, `headers: H` par
        `headers: authH()` pour que la RLS filtre par client une fois activée.
============================================================================ */
(function () {
  "use strict";

  // ------- RÉGLAGES -------
  const COMPTES_ACTIFS = false;              // <-- mettre true au cutover
  const STRIPE_ACTIF   = false;              // <-- mettre true quand compte Stripe créé
  const ADMIN_EMAILS   = ["bigandfranck89@gmail.com"];  // qui voit la Vitrine de validation
  const LS = "atelier_auth";

  // état d'authentification en mémoire
  let AUTH = null; // { access_token, refresh_token, email, uid, exp }

  // ------- utilitaires -------
  const b64json = t => { try { return JSON.parse(atob(t.split(".")[1].replace(/-/g,"+").replace(/_/g,"/"))); } catch (e) { return {}; } };

  function chargerAuth() {
    try {
      const j = JSON.parse(localStorage.getItem(LS) || "null");
      if (j && j.access_token && j.exp && j.exp * 1000 > Date.now() + 5000) { AUTH = j; return true; }
    } catch (e) {}
    return false;
  }
  function sauverAuth(tok) {
    const p = b64json(tok.access_token);
    AUTH = {
      access_token: tok.access_token,
      refresh_token: tok.refresh_token,
      email: (p.email || "").toLowerCase(),
      uid: p.sub,
      exp: p.exp
    };
    localStorage.setItem(LS, JSON.stringify(AUTH));
  }
  function deconnexion() { AUTH = null; localStorage.removeItem(LS); location.reload(); }

  // en-têtes à utiliser à la place de H : identité du client si connecté, sinon anon.
  window.authH = function () {
    const h = { apikey: KEY, "Content-Type": "application/json" };
    h.Authorization = "Bearer " + ((AUTH && AUTH.access_token) ? AUTH.access_token : KEY);
    return h;
  };
  window.atelierUser = () => AUTH;                                   // {email, uid} ou null

  // Mode Franck : déverrouille l'onglet Validation même quand les comptes sont
  // désactivés. Ouvrir l'app une seule fois avec ?admin=1 (ou #admin) suffit :
  // le déverrouillage est mémorisé sur le téléphone. ?admin=0 le retire.
  const LS_ADMIN = "atelier_admin";
  function majDeverrouillageAdmin() {
    try {
      const q = new URLSearchParams(location.search);
      const veut = q.get("admin");
      if (veut === "1" || location.hash === "#admin") localStorage.setItem(LS_ADMIN, "1");
      else if (veut === "0") localStorage.removeItem(LS_ADMIN);
    } catch (e) {}
  }
  function adminLocal() { try { return localStorage.getItem(LS_ADMIN) === "1"; } catch (e) { return false; } }
  window.estAdmin = () => adminLocal() || !!(AUTH && ADMIN_EMAILS.includes(AUTH.email));

  // rafraîchit le jeton si presque expiré (appelé au démarrage)
  async function rafraichirSiBesoin() {
    if (!AUTH || !AUTH.refresh_token) return;
    if (AUTH.exp * 1000 > Date.now() + 60000) return;
    try {
      const r = await fetch(`${SUPA}/auth/v1/token?grant_type=refresh_token`, {
        method: "POST", headers: { apikey: KEY, "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: AUTH.refresh_token })
      });
      if (r.ok) sauverAuth(await r.json()); else deconnexion();
    } catch (e) {}
  }

  // ------- GoTrue : code par e-mail (OTP) -------
  async function envoyerCode(email) {
    const r = await fetch(`${SUPA}/auth/v1/otp`, {
      method: "POST", headers: { apikey: KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ email: email, create_user: true })
    });
    if (!r.ok) throw new Error("envoi (" + r.status + ")");
  }
  async function verifierCode(email, code) {
    const r = await fetch(`${SUPA}/auth/v1/verify`, {
      method: "POST", headers: { apikey: KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ email: email, token: code.trim(), type: "email" })
    });
    if (!r.ok) throw new Error("code invalide");
    sauverAuth(await r.json());
    // crée/actualise la fiche client (ignore les erreurs : le bot la crée aussi)
    try {
      await fetch(`${SUPA}/rest/v1/studio_clients?on_conflict=email`, {
        method: "POST",
        headers: { ...authH(), Prefer: "resolution=merge-duplicates,return=minimal" },
        body: JSON.stringify({ id: AUTH.uid, email: AUTH.email, statut: "client" })
      });
    } catch (e) {}
  }

  // ------- écran de connexion (overlay) -------
  function overlayHTML() {
    return `
    <div id="auth-ov" style="position:fixed;inset:0;z-index:9999;background:#0f1115;display:flex;flex-direction:column;justify-content:center;align-items:center;padding:24px">
      <div style="font-size:40px">🧸</div>
      <h1 style="font-size:20px;margin:8px 0 4px">Atelier Figurines 3D</h1>
      <p style="color:#9aa0a6;font-size:14px;text-align:center;max-width:320px;margin-bottom:18px">Connecte-toi avec ton e-mail pour retrouver <b>tes</b> figurines. On t'envoie un code à 6 chiffres, pas de mot de passe.</p>
      <div style="width:100%;max-width:320px">
        <div id="auth-step1">
          <input id="auth-email" type="email" placeholder="ton@email.fr" autocomplete="email"
            style="width:100%;background:#0f1115;border:1px solid #2f3542;color:#fff;border-radius:12px;padding:12px 14px;font-size:15px;margin-bottom:8px">
          <button id="auth-send" style="width:100%;background:#2563eb;border:0;color:#fff;border-radius:12px;padding:12px;font-size:15px;font-weight:600;cursor:pointer">Recevoir mon code</button>
        </div>
        <div id="auth-step2" style="display:none">
          <input id="auth-code" inputmode="numeric" placeholder="Code à 6 chiffres"
            style="width:100%;background:#0f1115;border:1px solid #2f3542;color:#fff;border-radius:12px;padding:12px 14px;font-size:18px;letter-spacing:4px;text-align:center;margin-bottom:8px">
          <button id="auth-verify" style="width:100%;background:#16a34a;border:0;color:#fff;border-radius:12px;padding:12px;font-size:15px;font-weight:600;cursor:pointer">Me connecter</button>
          <button id="auth-back" style="width:100%;background:none;border:0;color:#9aa0a6;padding:10px;font-size:13px;cursor:pointer">← changer d'e-mail</button>
        </div>
        <div id="auth-msg" style="color:#ff9aa4;font-size:13px;margin-top:10px;text-align:center;min-height:18px"></div>
      </div>
    </div>`;
  }
  function montrerConnexion() {
    if ($("auth-ov")) return;
    document.body.insertAdjacentHTML("beforeend", overlayHTML());
    let email = "";
    const msg = t => { $("auth-msg").textContent = t || ""; };
    $("auth-send").onclick = async () => {
      email = ($("auth-email").value || "").trim().toLowerCase();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { msg("E-mail invalide."); return; }
      msg("Envoi du code…"); $("auth-send").disabled = true;
      try { await envoyerCode(email); $("auth-step1").style.display = "none"; $("auth-step2").style.display = "block"; msg("Code envoyé ! Regarde tes e-mails (et les spams)."); }
      catch (e) { msg("Impossible d'envoyer le code, réessaie."); }
      $("auth-send").disabled = false;
    };
    $("auth-verify").onclick = async () => {
      const code = ($("auth-code").value || "").trim();
      if (code.length < 6) { msg("Entre les 6 chiffres."); return; }
      msg("Vérification…"); $("auth-verify").disabled = true;
      try { await verifierCode(email, code); $("auth-ov").remove(); demarrerApp(); }
      catch (e) { msg("Code incorrect ou expiré. Renvoie un code si besoin."); }
      $("auth-verify").disabled = false;
    };
    $("auth-back").onclick = () => { $("auth-step2").style.display = "none"; $("auth-step1").style.display = "block"; msg(""); };
  }

  // ------- ce qui se lance une fois connecté (ou tout de suite si comptes off) -------
  function demarrerApp() {
    // bouton de déconnexion + Vitrine admin, injectés dans le header et la nav
    if (COMPTES_ACTIFS && AUTH) {
      const h = document.querySelector("header");
      if (h && !$("btn-logout")) {
        const b = document.createElement("button");
        b.id = "btn-logout"; b.title = "Se déconnecter"; b.textContent = "⎋";
        b.style.cssText = "background:#2a2f3a;color:#dbe4ff;border:0;border-radius:10px;padding:4px 10px;font-size:15px;cursor:pointer;margin-left:8px";
        b.onclick = deconnexion; h.appendChild(b);
      }
    }
    if (window.estAdmin && window.estAdmin()) activerVitrine();
    document.dispatchEvent(new CustomEvent("atelier-pret"));
  }

  // ============================ VITRINE DE VALIDATION ============================
  // Franck voit les propositions du jour (catalogue_propositions statut='propose')
  // et clique Garder / Rejeter. Preuve de solidité SANS impression : mesure de
  // l'épaisseur sur le vrai fichier 3D (>= 3 mm partout).
  function activerVitrine() {
    if ($("nav-valid")) return;
    const nav = document.querySelector("nav");
    if (nav) {
      const b = document.createElement("button");
      b.id = "nav-valid"; b.dataset.p = "valid";
      b.innerHTML = '<span class="ic">🗳️</span>Validation';
      b.onclick = () => {
        document.querySelectorAll("nav button").forEach(x => x.classList.remove("on"));
        document.querySelectorAll(".page").forEach(x => x.classList.remove("on"));
        b.classList.add("on"); $("p-valid").classList.add("on"); chargerValidation();
      };
      nav.appendChild(b);
    }
  }

  // Le contenu de l'onglet Validation vit dans validation/embed.js : ce fichier-ci
  // fait plus de 100 000 caracteres et ne peut etre republie qu'en entier, alors
  // que la validation demande des retouches frequentes. On charge donc le petit
  // fichier a la premiere ouverture de l'onglet, et lui dessine tout.
  window.SUPA_URL = SUPA;
  window.verdictEp = verdictEp;
  window.__validationAttendue = false;
  let validationDemandee = false;

  window.chargerValidation = function () {
    const zone = $("valid-zone"); if (!zone) return;
    if (validationDemandee) return;               // le vrai chargeur a pris la main
    validationDemandee = true;
    window.__validationAttendue = true;
    zone.innerHTML = `<p style="color:#9aa0a6;padding:14px">Chargement…</p>`;
    const sc = document.createElement("script");
    sc.src = "validation/embed.js?v=1";
    sc.onerror = () => {
      validationDemandee = false;
      zone.innerHTML = `<p style="color:#ff9aa4;padding:14px">Impossible de charger l'écran de validation (connexion ?).
        <button class="abtn sec" style="margin-top:10px" onclick="chargerValidation()">Réessayer</button></p>`;
    };
    document.head.appendChild(sc);
  };

  function verdictEp(mm) {
    mm = Number(mm);
    if (mm >= 3) return `<span style="color:#5be3a5">✅ Solide : parties fines ≈ ${mm.toFixed(1)} mm (≥ 3 mm partout).</span>`;
    if (mm >= 1.5) return `<span style="color:#ffcf7a">🟠 Fragile : ≈ ${mm.toFixed(1)} mm. À épaissir avant catalogue.</span>`;
    return `<span style="color:#ff9aa4">🔴 Trop fin : ≈ ${mm.toFixed(1)} mm — casserait. À corriger.</span>`;
  }

  window.mesurerSolidite = async function (id, url) {
    const el = $("ep-" + id); if (el) el.textContent = "Mesure de l'épaisseur sur le vrai fichier 3D… (10-20 s)";
    try {
      const { mesh, THREE } = await chargerMeshMM(url, 60); // hauteur de référence 60 mm
      const th = await mesureEpaisseurMM(THREE, mesh);
      if (!th) { if (el) el.textContent = "Mesure impossible sur ce fichier."; return; }
      const mm = th.p5;
      if (el) el.innerHTML = verdictEp(mm);
      // trace la mesure dans la proposition
      await fetch(`${SUPA}/rest/v1/catalogue_propositions?id=eq.${id}`, {
        method: "PATCH", headers: { ...authH(), Prefer: "return=minimal" },
        body: JSON.stringify({ epaisseur_min_mm: Number(mm.toFixed(2)) })
      });
    } catch (e) { if (el) el.textContent = "Erreur pendant la mesure (fichier 3D introuvable ?)."; }
  };

  // deciderProp est defini par validation/embed.js une fois celui-ci charge.

  // ============================ TARIFS + PAIEMENT (Stripe) ============================
  // Page tarifs prête ; le bouton Payer appelle l'Edge Function Stripe SEULEMENT si
  // STRIPE_ACTIF est true (sinon message "bientôt"). Voir stripe/README.
  window.payer = async function (offre) {
    if (!STRIPE_ACTIF) { alert("Le paiement en ligne arrive bientôt. Pour l'instant, on organise le règlement directement avec toi."); return; }
    if (COMPTES_ACTIFS && !AUTH) { montrerConnexion(); return; }
    try {
      const r = await fetch(`${SUPA}/functions/v1/stripe-checkout`, {
        method: "POST", headers: authH(),
        body: JSON.stringify({ offre: offre, email: AUTH ? AUTH.email : undefined })
      });
      const j = await r.json();
      if (j && j.url) location.href = j.url; else alert("Paiement indisponible pour l'instant.");
    } catch (e) { alert("Paiement indisponible pour l'instant."); }
  };

  // ------- démarrage -------
  async function init() {
    majDeverrouillageAdmin();
    chargerAuth();
    await rafraichirSiBesoin();
    if (COMPTES_ACTIFS && !AUTH) { montrerConnexion(); return; }
    demarrerApp();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

