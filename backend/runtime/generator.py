import json


def generate_runtime(schemas: dict, intent: dict) -> dict:
    """
    Generate a complete, self-contained working React application
    from the validated schemas. This is the 'runtime' layer that
    turns JSON config into an executable app.
    """
    app_name = intent.get("app_name", "My App")
    app_type = intent.get("app_type", "App")
    config_json = json.dumps(schemas, indent=2)

    html = _build_html(app_name, config_json)

    tables = schemas.get("db_schema", {}).get("tables", [])
    pages = schemas.get("ui_schema", {}).get("pages", [])
    roles = schemas.get("auth_schema", {}).get("roles", [])

    return {
        "html": html,
        "app_name": app_name,
        "app_type": app_type,
        "pages_generated": [p.get("name") for p in pages],
        "entities_generated": [t.get("name") for t in tables],
        "roles": roles,
        "features": [
            "Authentication with role-based access control",
            "Role-aware sidebar (each role sees only their pages)",
            "Per-role read / write / delete permission guards",
            "Access Denied page for restricted sections",
            "Dashboard with live stats",
            f"{len(tables)} entity CRUD pages",
            "Search & filter on all tables",
            "LocalStorage data persistence",
            "Add / Edit / Delete modals",
            "Responsive sidebar navigation",
        ],
    }


def _build_html(app_name: str, config_json: str) -> str:
    template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_name}</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
  <script>
    window.addEventListener("error", function(e) {
      document.body.innerHTML = "<div style='color:red; background:white; padding:20px; font-size:20px; z-index:9999; position:absolute; inset:0;'>" + e.message + "</div>";
    });
  </script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; height: 100vh; overflow: hidden; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #1e293b; }
    ::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
    input, select, textarea { font-family: inherit; }
    button { font-family: inherit; cursor: pointer; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script>window.APP_CONFIG = __CONFIG_JSON__;</script>
  <script type="text/babel">
    const { useState, useEffect, useCallback, useMemo } = React;

    /* ── Config ─────────────────────────────── */
    const CFG       = window.APP_CONFIG;
    const APP_NAME  = CFG?.intent?.app_name  || "__APP_NAME__";
    const TABLES    = CFG?.db_schema?.tables  || [];
    const AUTH      = CFG?.auth_schema        || {};
    const ROLES_CFG = AUTH.roles              || [];
    const ROLE_PERMS= AUTH.permissions        || {};
    const UI_PAGES  = CFG?.ui_schema?.pages   || [];

    /* ── Role permission helpers ─────────────── */
    // Build a map: { roleName: { tableName: { read, write, delete } } }
    // We derive permissions from auth_schema.permissions if available,
    // otherwise fall back to sensible defaults based on role position.
    const buildRolePermMap = () => {
      const map = {};
      const adminRoles   = ["admin", "administrator", "superadmin", "owner"];
      const readOnlyRoles= ["viewer", "guest", "readonly", "analyst", "reporter"];
      const writeRoles   = ["manager", "editor", "staff", "receptionist", "teacher", "doctor", "nurse", "seller", "agent"];

      ROLES_CFG.forEach((role, idx) => {
        const rLower = role.toLowerCase();
        const isAdmin    = adminRoles.some(a => rLower.includes(a)) || idx === 0;
        const isReadOnly = !isAdmin && readOnlyRoles.some(a => rLower.includes(a));
        const isWriter   = !isAdmin && !isReadOnly;

        // Check if we have explicit permissions in the schema
        const explicit = ROLE_PERMS[role] || ROLE_PERMS[rLower] || null;

        map[role] = {};
        TABLES.forEach(t => {
          if (explicit && explicit[t.name]) {
            map[role][t.name] = explicit[t.name];
          } else if (explicit && explicit["*"]) {
            map[role][t.name] = explicit["*"];
          } else {
            // Infer permissions
            // Admins: full access. Writers: read+write only. ReadOnly: read only.
            // Special: "users" table restricted for non-admins.
            const isUsersTable = t.name.toLowerCase() === "users";
            if (isAdmin) {
              map[role][t.name] = { read: true, write: true, delete: true, visible: true };
            } else if (isUsersTable) {
              // Non-admins can't manage users table
              map[role][t.name] = { read: false, write: false, delete: false, visible: false };
            } else if (isWriter) {
              map[role][t.name] = { read: true, write: true, delete: false, visible: true };
            } else {
              // read-only
              map[role][t.name] = { read: true, write: false, delete: false, visible: true };
            }
          }
        });
      });
      return map;
    };

    const PERM_MAP = buildRolePermMap();

    const getPerm = (role, table) => {
      return PERM_MAP[role]?.[table] || { read: false, write: false, delete: false, visible: false };
    };

    const canRead   = (role, table) => getPerm(role, table).read   !== false;
    const canWrite  = (role, table) => getPerm(role, table).write  === true;
    const canDelete = (role, table) => getPerm(role, table).delete === true;
    const canSee    = (role, table) => getPerm(role, table).visible !== false;

    /* ── LocalStorage DB ─────────────────────── */
    const genId = () => Date.now().toString(36) + Math.random().toString(36).slice(2);
    const db = {
      getAll : (t)       => JSON.parse(localStorage.getItem("db_" + t) || "[]"),
      save   : (t, rows) => localStorage.setItem("db_" + t, JSON.stringify(rows)),
      insert : (t, row)  => {
        const rows = db.getAll(t);
        const nr = { id: genId(), created_at: new Date().toISOString(), updated_at: new Date().toISOString(), ...row };
        db.save(t, [...rows, nr]);
        return nr;
      },
      update : (t, id, u) => {
        db.save(t, db.getAll(t).map(r => r.id === id ? { ...r, ...u, updated_at: new Date().toISOString() } : r));
      },
      remove : (t, id)   => db.save(t, db.getAll(t).filter(r => r.id !== id)),
    };

    /* ── Styles ─────────────────────────────── */
    const c = {
      app        : { display:"flex", height:"100vh", background:"#0f172a", color:"#e2e8f0", overflow:"hidden" },
      sidebar    : { width:240, background:"#1e293b", borderRight:"1px solid #334155", display:"flex", flexDirection:"column", flexShrink:0, overflowY:"auto" },
      sbHead     : { padding:"20px 16px 16px", borderBottom:"1px solid #334155" },
      sbTitle    : { fontSize:17, fontWeight:700, color:"#f1f5f9", display:"flex", alignItems:"center", gap:8 },
      sbSub      : { fontSize:11, color:"#64748b", marginTop:2 },
      sbSection  : { fontSize:10, color:"#475569", textTransform:"uppercase", letterSpacing:"0.08em", padding:"14px 16px 4px", fontWeight:700 },
      nav        : { padding:"8px 0", flex:1 },
      navItem    : (a) => ({ display:"flex", alignItems:"center", gap:10, padding:"9px 14px", cursor:"pointer", borderRadius:8, margin:"2px 8px", background: a ? "linear-gradient(135deg,#6366f1,#7c3aed)" : "transparent", color: a ? "#fff" : "#94a3b8", fontSize:13, fontWeight: a ? 600 : 400, transition:"all 0.15s", boxShadow: a ? "0 2px 12px #6366f155" : "none" }),
      main       : { flex:1, overflowY:"auto", padding:"28px 32px" },
      pageTitle  : { fontSize:26, fontWeight:700, color:"#f1f5f9", marginBottom:4 },
      pageSub    : { fontSize:13, color:"#64748b", marginBottom:24 },
      card       : { background:"#1e293b", border:"1px solid #334155", borderRadius:12, padding:20, marginBottom:20 },
      statGrid   : { display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(160px,1fr))", gap:14, marginBottom:24 },
      stat       : { background:"#1e293b", border:"1px solid #334155", borderRadius:12, padding:"18px 20px" },
      statVal    : { fontSize:30, fontWeight:700, color:"#6366f1" },
      statLbl    : { fontSize:11, color:"#64748b", marginTop:4, textTransform:"uppercase", letterSpacing:"0.05em" },
      btn        : (v) => ({ padding:"8px 16px", borderRadius:8, border:"none", cursor:"pointer", fontSize:13, fontWeight:600, transition:"opacity 0.15s",
                    background: v==="primary" ? "linear-gradient(135deg,#6366f1,#7c3aed)" : v==="danger" ? "#ef4444" : v==="warning" ? "#f59e0b" : "#334155",
                    color:"#fff", boxShadow: v==="primary" ? "0 2px 12px #6366f144" : "none" }),
      table      : { width:"100%", borderCollapse:"collapse" },
      th         : { textAlign:"left", padding:"10px 14px", fontSize:11, color:"#64748b", textTransform:"uppercase", letterSpacing:"0.06em", borderBottom:"1px solid #334155", whiteSpace:"nowrap" },
      td         : { padding:"12px 14px", fontSize:13, color:"#e2e8f0", borderBottom:"1px solid #1e293b", whiteSpace:"nowrap", maxWidth:200, overflow:"hidden", textOverflow:"ellipsis" },
      input      : { width:"100%", background:"#0f172a", border:"1px solid #334155", borderRadius:8, padding:"9px 12px", color:"#e2e8f0", fontSize:13, outline:"none", marginBottom:12 },
      label      : { fontSize:11, color:"#94a3b8", fontWeight:600, marginBottom:4, display:"block", textTransform:"uppercase", letterSpacing:"0.05em" },
      overlay    : { position:"fixed", inset:0, background:"rgba(0,0,0,0.75)", display:"flex", alignItems:"center", justifyContent:"center", zIndex:1000 },
      modal      : { background:"#1e293b", border:"1px solid #475569", borderRadius:16, padding:28, width:460, maxHeight:"85vh", overflowY:"auto" },
      badge      : (col) => ({ display:"inline-flex", alignItems:"center", padding:"2px 10px", borderRadius:999, fontSize:11, fontWeight:600, background: col+"22", color: col, border:"1px solid "+col+"44" }),
      userArea   : { marginTop:"auto", padding:"14px 12px", borderTop:"1px solid #334155" },
      avatar     : (col) => ({ width:32, height:32, borderRadius:"50%", background: col || "linear-gradient(135deg,#6366f1,#7c3aed)", display:"flex", alignItems:"center", justifyContent:"center", color:"#fff", fontWeight:700, fontSize:13, flexShrink:0 }),
      loginWrap  : { display:"flex", alignItems:"center", justifyContent:"center", height:"100vh", background:"#0f172a" },
      loginCard  : { background:"#1e293b", border:"1px solid #334155", borderRadius:20, padding:40, width:380, boxShadow:"0 20px 60px rgba(0,0,0,0.5)" },
      accessDenied:{ display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", height:"60vh", gap:16 },
      permTag    : (ok) => ({ display:"inline-flex", alignItems:"center", gap:4, padding:"3px 10px", borderRadius:999, fontSize:11, fontWeight:600,
                    background: ok ? "#10b98122" : "#ef444422", color: ok ? "#34d399" : "#fca5a5", border: "1px solid " + (ok ? "#10b98144" : "#ef444444") }),
    };

    /* ── Badge color helper ─────────────────── */
    const statusColor = (val) => {
      const v = String(val).toLowerCase();
      if (["active","won","completed","success","open","qualified","approved","available"].includes(v)) return "#10b981";
      if (["inactive","lost","failed","cancelled","closed","rejected","unavailable"].includes(v)) return "#ef4444";
      if (["pending","prospect","in_progress","negotiation","proposal","scheduled","review"].includes(v)) return "#f59e0b";
      if (["admin","administrator","superadmin"].includes(v)) return "#8b5cf6";
      if (["manager","supervisor","lead"].includes(v)) return "#6366f1";
      if (["doctor","nurse","physician"].includes(v)) return "#06b6d4";
      if (["teacher","instructor","professor"].includes(v)) return "#10b981";
      return "#6366f1";
    };

    const roleColor = (role) => {
      const r = (role || "").toLowerCase();
      if (["admin","administrator","superadmin","owner"].some(x => r.includes(x))) return "linear-gradient(135deg,#8b5cf6,#7c3aed)";
      if (["manager","supervisor","lead"].some(x => r.includes(x))) return "linear-gradient(135deg,#6366f1,#4f46e5)";
      if (["doctor","physician"].some(x => r.includes(x))) return "linear-gradient(135deg,#06b6d4,#0891b2)";
      if (["teacher","instructor"].some(x => r.includes(x))) return "linear-gradient(135deg,#10b981,#059669)";
      if (["receptionist","staff","nurse"].some(x => r.includes(x))) return "linear-gradient(135deg,#f59e0b,#d97706)";
      return "linear-gradient(135deg,#64748b,#475569)";
    };

    const ICONS = {
      dashboard:"📊", contacts:"👥", users:"👤", deals:"💼", activity:"📋",
      orders:"🛒", products:"📦", employees:"👔", patients:"🏥", courses:"📚",
      appointments:"📅", doctors:"🩺", nurses:"💉", teachers:"🎓", students:"🎒",
      reports:"📈", analytics:"📉", analytics_reports:"📉", invoices:"🧾",
      tasks:"✅", projects:"🗂️", tickets:"🎫", payments:"💳", inventory:"🏬",
      grades:"📝", enrollments:"📋", departments:"🏢", default:"📄"
    };
    const icon = (name) => ICONS[name?.toLowerCase()] || ICONS.default;
    const titleCase = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g," ") : "";
    const userFields = (fields) => (fields||[]).filter(f => !["id","created_at","updated_at"].includes(f.name));

    /* ══════════════════════════════════════════
       LOGIN PAGE
    ══════════════════════════════════════════ */
    function LoginPage({ onLogin }) {
      const [email, setEmail]       = useState("admin@app.com");
      const [password, setPassword] = useState("password");
      const [role, setRole]         = useState(ROLES_CFG[0] || "admin");
      const [error, setError]       = useState("");

      const handleLogin = (e) => {
        e.preventDefault();
        if (!email || !password) { setError("Please fill in all fields"); return; }
        onLogin({ email, role, name: email.split("@")[0] });
      };

      return (
        <div style={c.loginWrap}>
          <div style={c.loginCard}>
            <div style={{textAlign:"center", marginBottom:28}}>
              <div style={{fontSize:36, marginBottom:10}}>⚡</div>
              <div style={{fontSize:22, fontWeight:700, color:"#f1f5f9"}}>{APP_NAME}</div>
              <div style={{fontSize:13, color:"#64748b", marginTop:4}}>Sign in to continue</div>
            </div>
            {error && <div style={{background:"#ef444422", border:"1px solid #ef4444", borderRadius:8, padding:"8px 12px", color:"#fca5a5", fontSize:12, marginBottom:14}}>{error}</div>}
            <form onSubmit={handleLogin}>
              <label style={c.label}>Email</label>
              <input style={c.input} value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
              <label style={c.label}>Password</label>
              <input style={c.input} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
              <label style={c.label}>Role</label>
              <select style={{...c.input, marginBottom:20}} value={role} onChange={e => setRole(e.target.value)}>
                {ROLES_CFG.map(r => <option key={r} value={r}>{titleCase(r)}</option>)}
              </select>
              <button type="submit" style={{...c.btn("primary"), width:"100%", padding:"11px"} }>Sign In →</button>
            </form>
            <div style={{fontSize:11, color:"#475569", textAlign:"center", marginTop:16}}>
              Generated by AI App Compiler
            </div>
          </div>
        </div>
      );
    }

    /* ══════════════════════════════════════════
       MODAL
    ══════════════════════════════════════════ */
    function Modal({ title, onClose, children }) {
      return (
        <div style={c.overlay} onClick={e => e.target === e.currentTarget && onClose()}>
          <div style={c.modal}>
            <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:20}}>
              <h3 style={{color:"#f1f5f9", fontWeight:700, fontSize:16}}>{title}</h3>
              <button onClick={onClose} style={{background:"none", border:"none", color:"#64748b", fontSize:20, cursor:"pointer", lineHeight:1}} >✕</button>
            </div>
            {children}
          </div>
        </div>
      );
    }

    /* ══════════════════════════════════════════
       ACCESS DENIED
    ══════════════════════════════════════════ */
    function AccessDenied({ tableName, role }) {
      return (
        <div style={c.accessDenied}>
          <div style={{fontSize:64}}>🔒</div>
          <div style={{fontSize:22, fontWeight:700, color:"#f1f5f9"}}>Access Restricted</div>
          <div style={{fontSize:14, color:"#64748b", textAlign:"center", maxWidth:320}}>
            Your role <strong style={{color: statusColor(role)}}>{titleCase(role)}</strong> does not have permission to view <strong style={{color:"#818cf8"}}>{titleCase(tableName)}</strong>.
          </div>
          <div style={{fontSize:12, color:"#475569", background:"#1e293b", border:"1px solid #334155", padding:"10px 20px", borderRadius:8}}>
            Contact an administrator to request access.
          </div>
        </div>
      );
    }

    /* ══════════════════════════════════════════
       PERMISSION BADGE ROW (shown in entity page header)
    ══════════════════════════════════════════ */
    function PermBadges({ role, tableName }) {
      const p = getPerm(role, tableName);
      return (
        <div style={{display:"flex", gap:6, alignItems:"center", marginTop:6, flexWrap:"wrap"}}>
          <span style={{fontSize:11, color:"#475569"}}>Your permissions:</span>
          <span style={c.permTag(p.read)}>  {p.read  ? "✓" : "✗"} Read</span>
          <span style={c.permTag(p.write)}> {p.write ? "✓" : "✗"} Write</span>
          <span style={c.permTag(p.delete)}>{p.delete? "✓" : "✗"} Delete</span>
        </div>
      );
    }

    /* ══════════════════════════════════════════
       ENTITY CRUD PAGE (RBAC-aware)
    ══════════════════════════════════════════ */
    function EntityPage({ table, user }) {
      const role = user.role;
      const perm = getPerm(role, table.name);

      // Access denied if can't read
      if (!perm.read) return <AccessDenied tableName={table.name} role={role} />;

      const [rows, setRows]       = useState([]);
      const [modal, setModal]     = useState(false);
      const [editing, setEditing] = useState(null);
      const [form, setForm]       = useState({});
      const [search, setSearch]   = useState("");

      const uf = userFields(table.fields);
      const refresh = useCallback(() => setRows(db.getAll(table.name)), [table.name]);
      useEffect(() => { refresh(); }, [refresh]);

      const openAdd  = () => { setForm({}); setEditing(null); setModal(true); };
      const openEdit = (row) => { setForm({...row}); setEditing(row.id); setModal(true); };
      const handleDelete = (id) => {
        if (!perm.delete) return;
        if (window.confirm("Delete this record?")) { db.remove(table.name, id); refresh(); }
      };
      const handleSave = () => {
        if (!perm.write) return;
        if (editing) db.update(table.name, editing, form);
        else db.insert(table.name, form);
        refresh(); setModal(false);
      };

      const filtered = useMemo(() => rows.filter(r =>
        uf.some(f => String(r[f.name] || "").toLowerCase().includes(search.toLowerCase()))
      ), [rows, search, uf]);

      const isStatusField = (name) => ["status","role","type","stage","state","priority","gender"].includes(name.toLowerCase());

      return (
        <div>
          <div style={{display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:20}}>
            <div>
              <div style={c.pageTitle}>{icon(table.name)} {titleCase(table.name)}</div>
              <div style={{fontSize:13, color:"#64748b"}}>{filtered.length} record{filtered.length !== 1 ? "s" : ""}</div>
              <PermBadges role={role} tableName={table.name} />
            </div>
            {perm.write && (
              <button style={c.btn("primary")} onClick={openAdd}>+ Add {titleCase(table.name)}</button>
            )}
          </div>

          <div style={c.card}>
            <input
              style={{...c.input, width:280, marginBottom:16}}
              placeholder={`Search ${table.name}...`}
              value={search} onChange={e => setSearch(e.target.value)}
            />
            <div style={{overflowX:"auto"}}>
              <table style={c.table}>
                <thead>
                  <tr>
                    {uf.slice(0,6).map(f => <th key={f.name} style={c.th}>{f.name.replace(/_/g," ")}</th>)}
                    {(perm.write || perm.delete) && <th style={c.th}>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr><td colSpan={uf.length + 1} style={{...c.td, textAlign:"center", color:"#475569", padding:40}}>
                      {perm.write ? 'No records yet. Click "+ Add" to create one.' : "No records found."}
                    </td></tr>
                  ) : filtered.map(row => (
                    <tr key={row.id} style={{transition:"background 0.1s"}}
                      onMouseEnter={e => e.currentTarget.style.background="#ffffff08"}
                      onMouseLeave={e => e.currentTarget.style.background=""}>
                      {uf.slice(0,6).map(f => (
                        <td key={f.name} style={c.td} title={String(row[f.name]||"")}>
                          {isStatusField(f.name) && row[f.name]
                            ? <span style={c.badge(statusColor(row[f.name]))}>{String(row[f.name])}</span>
                            : f.type === "boolean" ? (row[f.name] ? "✓ Yes" : "✗ No")
                            : String(row[f.name] || "—")}
                        </td>
                      ))}
                      {(perm.write || perm.delete) && (
                        <td style={c.td}>
                          {perm.write  && <button style={{...c.btn("secondary"), padding:"4px 10px", marginRight:6, fontSize:12}} onClick={() => openEdit(row)}>Edit</button>}
                          {perm.delete && <button style={{...c.btn("danger"),    padding:"4px 10px", fontSize:12}} onClick={() => handleDelete(row.id)}>Delete</button>}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {modal && perm.write && (
            <Modal title={editing ? `Edit ${titleCase(table.name)}` : `New ${titleCase(table.name)}`} onClose={() => setModal(false)}>
              {uf.map(f => (
                <div key={f.name}>
                  <label style={c.label}>{f.name.replace(/_/g," ")}{f.required ? " *" : ""}</label>
                  {f.type === "boolean"
                    ? <select style={c.input} value={String(form[f.name]||"false")} onChange={e => setForm(p => ({...p, [f.name]: e.target.value === "true"}))}>
                        <option value="true">Yes</option><option value="false">No</option>
                      </select>
                    : f.type === "text"
                    ? <textarea style={{...c.input, minHeight:80, resize:"vertical"}} value={form[f.name]||""} onChange={e => setForm(p => ({...p,[f.name]:e.target.value}))} placeholder={f.name.replace(/_/g," ")} />
                    : <input style={c.input}
                        type={f.type==="integer"||f.type==="float" ? "number" : f.type==="datetime" ? "datetime-local" : "text"}
                        placeholder={f.name.replace(/_/g," ")}
                        value={form[f.name]||""}
                        onChange={e => setForm(p => ({...p,[f.name]:e.target.value}))}
                      />
                  }
                </div>
              ))}
              <div style={{display:"flex", gap:8, marginTop:8}}>
                <button style={{...c.btn("primary"), flex:1}} onClick={handleSave}>Save</button>
                <button style={{...c.btn("secondary"), flex:1}} onClick={() => setModal(false)}>Cancel</button>
              </div>
            </Modal>
          )}
        </div>
      );
    }

    /* ══════════════════════════════════════════
       DASHBOARD
    ══════════════════════════════════════════ */
    function Dashboard({ user }) {
      const role = user.role;
      const [counts, setCounts] = useState({});

      // Only count tables this role can see
      const visibleTables = TABLES.filter(t => canSee(role, t.name) && canRead(role, t.name));

      useEffect(() => {
        const c2 = {};
        TABLES.forEach(t => { c2[t.name] = db.getAll(t.name).length; });
        setCounts(c2);
      }, []);

      const recent = useMemo(() => visibleTables.flatMap(t =>
        db.getAll(t.name).slice(-2).map(r => ({ table: t.name, created: r.created_at || "" }))
      ).sort((a,b) => b.created.localeCompare(a.created)).slice(0,6), [counts]);

      // Role-specific welcome messages
      const roleWelcome = () => {
        const r = role.toLowerCase();
        if (r.includes("admin")) return "You have full system access.";
        if (r.includes("doctor") || r.includes("physician")) return "View your assigned patients and appointments.";
        if (r.includes("nurse")) return "Manage patient care and appointments.";
        if (r.includes("receptionist")) return "Manage patient bookings and appointments.";
        if (r.includes("teacher") || r.includes("instructor")) return "Manage your courses and student grades.";
        if (r.includes("student")) return "View your courses and academic records.";
        if (r.includes("manager")) return "Oversee team operations and reports.";
        if (r.includes("analyst") || r.includes("viewer")) return "You have read-only access to reports.";
        return `Welcome to ${APP_NAME}.`;
      };

      return (
        <div>
          <div style={c.pageTitle}>Welcome back, {user.name}! 👋</div>
          <div style={{fontSize:13, color:"#64748b", marginBottom:24}}>{roleWelcome()}</div>

          {/* Role info card */}
          <div style={{...c.card, background:"linear-gradient(135deg,#1e1b4b,#1e293b)", border:"1px solid #6366f133", marginBottom:20}}>
            <div style={{display:"flex", alignItems:"center", gap:12}}>
              <div style={{...c.avatar(roleColor(role)), width:44, height:44, fontSize:18}}>
                {user.name[0].toUpperCase()}
              </div>
              <div>
                <div style={{fontSize:14, fontWeight:700, color:"#f1f5f9"}}>{user.name}</div>
                <div style={{display:"flex", alignItems:"center", gap:8, marginTop:4}}>
                  <span style={c.badge(statusColor(role))}>{titleCase(role)}</span>
                  <span style={{fontSize:12, color:"#64748b"}}>{user.email}</span>
                </div>
              </div>
              <div style={{marginLeft:"auto", textAlign:"right"}}>
                <div style={{fontSize:11, color:"#475569", marginBottom:6}}>Accessible sections</div>
                <div style={{fontSize:20, fontWeight:700, color:"#818cf8"}}>{visibleTables.length + 1}</div>
              </div>
            </div>
          </div>

          {/* Stats — only visible tables */}
          <div style={c.statGrid}>
            {visibleTables.map(t => (
              <div key={t.name} style={c.stat}>
                <div style={{fontSize:22, marginBottom:6}}>{icon(t.name)}</div>
                <div style={c.statVal}>{counts[t.name] || 0}</div>
                <div style={c.statLbl}>{titleCase(t.name)}</div>
              </div>
            ))}
          </div>

          {/* Recent Activity */}
          <div style={c.card}>
            <div style={{fontWeight:600, color:"#f1f5f9", marginBottom:16, fontSize:14}}>Recent Activity</div>
            {recent.length === 0
              ? <div style={{color:"#475569", textAlign:"center", padding:20, fontSize:13}}>No activity yet. Start adding records!</div>
              : recent.map((a,i) => (
                  <div key={i} style={{display:"flex", justifyContent:"space-between", alignItems:"center", padding:"10px 0", borderBottom: i < recent.length-1 ? "1px solid #334155" : "none"}}>
                    <span style={{fontSize:13, color:"#94a3b8"}}>{icon(a.table)} New record in <strong style={{color:"#818cf8"}}>{titleCase(a.table)}</strong></span>
                    <span style={{fontSize:11, color:"#475569"}}>{a.created ? new Date(a.created).toLocaleString() : "just now"}</span>
                  </div>
                ))
            }
          </div>

          {/* My Permissions summary */}
          <div style={c.card}>
            <div style={{fontWeight:600, color:"#f1f5f9", marginBottom:16, fontSize:14}}>🛡️ My Permissions</div>
            <table style={c.table}>
              <thead>
                <tr>
                  <th style={c.th}>Section</th>
                  <th style={c.th}>Read</th>
                  <th style={c.th}>Write</th>
                  <th style={c.th}>Delete</th>
                </tr>
              </thead>
              <tbody>
                {TABLES.map(t => {
                  const p = getPerm(role, t.name);
                  return (
                    <tr key={t.name}>
                      <td style={c.td}>{icon(t.name)} {titleCase(t.name)}</td>
                      <td style={c.td}><span style={c.permTag(p.read)}>{p.read ? "✓ Yes" : "✗ No"}</span></td>
                      <td style={c.td}><span style={c.permTag(p.write)}>{p.write ? "✓ Yes" : "✗ No"}</span></td>
                      <td style={c.td}><span style={c.permTag(p.delete)}>{p.delete ? "✓ Yes" : "✗ No"}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    /* ══════════════════════════════════════════
       SIDEBAR  (role-aware)
    ══════════════════════════════════════════ */
    function Sidebar({ current, setCurrent, user, onLogout }) {
      const role = user.role;

      // Visible nav items = tables this role can read
      const visibleTables = TABLES.filter(t => canSee(role, t.name) && canRead(role, t.name));
      const hiddenTables  = TABLES.filter(t => !canSee(role, t.name) || !canRead(role, t.name));

      return (
        <div style={c.sidebar}>
          <div style={c.sbHead}>
            <div style={c.sbTitle}><span style={{fontSize:20}}>⚡</span>{APP_NAME}</div>
            <div style={c.sbSub}>AI Generated App</div>
          </div>
          <nav style={c.nav}>
            <div style={c.sbSection}>Main</div>
            <div style={c.navItem(current==="dashboard")} onClick={() => setCurrent("dashboard")}>
              <span style={{fontSize:16}}>📊</span>
              <span>Dashboard</span>
            </div>

            {visibleTables.length > 0 && <div style={c.sbSection}>My Sections</div>}
            {visibleTables.map(t => (
              <div key={t.name} style={c.navItem(current===t.name)} onClick={() => setCurrent(t.name)}>
                <span style={{fontSize:16}}>{icon(t.name)}</span>
                <span>{titleCase(t.name)}</span>
                {!canWrite(role, t.name) && (
                  <span style={{marginLeft:"auto", fontSize:10, color:"#475569", background:"#1e293b", padding:"1px 5px", borderRadius:4}}>read</span>
                )}
              </div>
            ))}

            {hiddenTables.length > 0 && (
              <>
                <div style={c.sbSection}>Restricted</div>
                {hiddenTables.map(t => (
                  <div key={t.name} style={{...c.navItem(false), opacity:0.35, cursor:"not-allowed"}} title="No access">
                    <span style={{fontSize:16}}>🔒</span>
                    <span>{titleCase(t.name)}</span>
                  </div>
                ))}
              </>
            )}
          </nav>

          <div style={c.userArea}>
            <div style={{display:"flex", alignItems:"center", gap:10, marginBottom:10}}>
              <div style={c.avatar(roleColor(role))}>{user.name[0].toUpperCase()}</div>
              <div>
                <div style={{fontSize:13, fontWeight:600, color:"#f1f5f9"}}>{user.name}</div>
                <div style={{fontSize:11, color:"#6366f1"}}>{titleCase(role)}</div>
              </div>
            </div>
            <button style={{...c.btn("secondary"), width:"100%", fontSize:12, padding:"7px"}} onClick={onLogout}>Sign Out</button>
          </div>
        </div>
      );
    }

    /* ══════════════════════════════════════════
       ROOT APP
    ══════════════════════════════════════════ */
    function App() {
      const [user, setUser]       = useState(null);
      const [current, setCurrent] = useState("dashboard");

      if (!user) return <LoginPage onLogin={setUser} />;

      const currentTable = TABLES.find(t => t.name === current);

      return (
        <div style={c.app}>
          <Sidebar current={current} setCurrent={setCurrent} user={user} onLogout={() => { setUser(null); setCurrent("dashboard"); }} />
          <main style={c.main}>
            {current === "dashboard" && <Dashboard user={user} />}
            {currentTable && <EntityPage table={currentTable} user={user} />}
          </main>
        </div>
      );
    }

    class ErrorBoundary extends React.Component {
      constructor(props) { super(props); this.state = { hasError: false, error: null }; }
      static getDerivedStateFromError(error) { return { hasError: true, error }; }
      render() {
        if (this.state.hasError) return <div style={{color:'red', background:'white', padding:20, fontSize:20}}>React Error: {this.state.error.message}</div>;
        return this.props.children;
      }
    }

    ReactDOM.createRoot(document.getElementById("root")).render(<ErrorBoundary><App /></ErrorBoundary>);
  </script>

</body>
</html>
"""
    return template.replace("__APP_NAME__", app_name).replace("__CONFIG_JSON__", config_json)
