"""Generate architecture, class, and ERD diagrams (graphviz) — large, legible text."""
import os, subprocess

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrams")
os.makedirs(OUT, exist_ok=True)
INK="#22303c"; ACCENT="#7c2d2d"; FILL2="#e7eef2"; LINE="#5c6b76"

# ---------------------------------------------------------------- architecture
architecture = f'''
digraph G {{
  rankdir=TB; bgcolor="white";
  graph [fontname="Helvetica", dpi=200, ranksep=0.55, nodesep=0.40];
  node  [fontname="Helvetica", shape=box, style="rounded,filled", color="{LINE}",
         fontcolor="{INK}", penwidth=1.4, fontsize=15, margin="0.22,0.12"];
  edge  [color="{LINE}", fontname="Helvetica", fontsize=12, arrowsize=0.9, penwidth=1.4];
  subgraph cluster_p {{
    label="Presentation Layer  (Jinja2 templates + CSS)"; style="rounded,filled";
    color="{LINE}"; fillcolor="{FILL2}"; fontname="Helvetica-Bold"; fontsize=15;
    browser [label="Reader / Admin\\nWeb Browser", fillcolor="white"];
    views   [label="Rendered Views\\nDashboard | Catalogue | Detail | Admin", fillcolor="white"];
  }}
  subgraph cluster_b {{
    label="Business Logic Layer  (Flask)"; style="rounded,filled";
    color="{LINE}"; fillcolor="#efe7da"; fontname="Helvetica-Bold"; fontsize=15;
    auth  [label="auth\\nblueprint", fillcolor="white"];
    main  [label="main\\nblueprint", fillcolor="white"];
    admin [label="admin\\nblueprint", fillcolor="white"];
    engine [label="Recommendation Engine\\n(collaborative filtering)", fillcolor="#f0dede", color="{ACCENT}", fontcolor="{ACCENT}"];
  }}
  subgraph cluster_d {{
    label="Data Access Layer"; style="rounded,filled";
    color="{LINE}"; fillcolor="{FILL2}"; fontname="Helvetica-Bold"; fontsize=15;
    orm [label="SQLAlchemy ORM\\nUser | Book | Rating", fillcolor="white"];
    db  [label="Database\\n(SQLite / MySQL)", shape=cylinder, fillcolor="white"];
  }}
  pandas [label="Pandas / NumPy\\nmatrix + similarity", fillcolor="#f0dede", color="{ACCENT}", fontcolor="{ACCENT}"];
  browser -> views [dir=both];
  views -> auth; views -> main; views -> admin;
  main -> engine; admin -> engine;
  engine -> pandas [dir=both, label=" ratings\\n matrix"];
  auth -> orm; main -> orm; admin -> orm; engine -> orm;
  orm -> db [dir=both];
}}
'''

# ---------------------------------------------------------------- class (2x2)
def crow(rows):
    return "".join(rows)
class_diagram = f'''
digraph G {{
  rankdir=TB; bgcolor="white"; splines=true;
  graph [fontname="Helvetica", dpi=200, ranksep=1.1, nodesep=1.0];
  node  [fontname="Helvetica", shape=plaintext, fontsize=14];
  edge  [fontname="Helvetica", fontsize=13, color="{LINE}", penwidth=1.5];

  User [label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="7" bgcolor="white">
      <tr><td bgcolor="{INK}"><font color="white" point-size="16"><b>User</b></font></td></tr>
      <tr><td align="left">- id : int<br align="left"/>- name : str<br align="left"/>- email : str<br align="left"/>- password_hash : str<br align="left"/>- is_admin : bool<br align="left"/>- bio : str<br align="left"/></td></tr>
      <tr><td align="left">+ set_password(pw)<br align="left"/>+ check_password(pw) : bool<br align="left"/>+ rated_book_ids() : set<br align="left"/></td></tr>
    </table>>];
  Book [label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="7" bgcolor="white">
      <tr><td bgcolor="{INK}"><font color="white" point-size="16"><b>Book</b></font></td></tr>
      <tr><td align="left">- id : int<br align="left"/>- title : str<br align="left"/>- author : str<br align="left"/>- genre : str<br align="left"/>- year : int<br align="left"/>- isbn : str<br align="left"/></td></tr>
      <tr><td align="left">+ average_rating() : float<br align="left"/>+ rating_count() : int<br align="left"/>+ reviews() : list<br align="left"/></td></tr>
    </table>>];
  Rating [label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="7" bgcolor="white">
      <tr><td bgcolor="{ACCENT}"><font color="white" point-size="16"><b>Rating</b></font></td></tr>
      <tr><td align="left">- id : int<br align="left"/>- user_id : FK<br align="left"/>- book_id : FK<br align="left"/>- score : int (1..5)<br align="left"/>- review : str<br align="left"/>- created_at : datetime<br align="left"/></td></tr>
      <tr><td align="left">unique(user_id, book_id)</td></tr>
    </table>>];
  Engine [label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="7" bgcolor="white">
      <tr><td bgcolor="{ACCENT}"><font color="white" point-size="16"><b>RecommendationEngine</b></font></td></tr>
      <tr><td align="left">- method : str<br align="left"/>- top_n : int<br align="left"/>- min_overlap : int<br align="left"/>- n_neighbours : int<br align="left"/></td></tr>
      <tr><td align="left">+ recommend_for(user_id) : list<br align="left"/>+ invalidate()<br align="left"/>- _explain(...)<br align="left"/>- _popularity_recs(...)<br align="left"/></td></tr>
    </table>>];

  {{ rank=same; User; Book }}
  {{ rank=same; Rating; Engine }}
  User -> Rating [taillabel="1", headlabel="0..*", arrowhead=none, labeldistance=2.0, labelangle=18];
  Book -> Rating [taillabel="1", headlabel="0..*", arrowhead=none, labeldistance=2.0, labelangle=-18];
  Engine -> Rating [style=dashed, arrowhead=vee, label="reads"];
  Engine -> Book   [style=dashed, arrowhead=vee, label="resolves"];
}}
'''

# ---------------------------------------------------------------- ERD
erd = f'''
digraph G {{
  rankdir=TB; bgcolor="white";
  graph [fontname="Helvetica", dpi=200, ranksep=1.2, nodesep=1.1];
  node  [fontname="Helvetica", shape=plaintext, fontsize=14];
  edge  [fontname="Helvetica", fontsize=14, color="{LINE}", penwidth=1.6];

  users [label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="7" bgcolor="white">
      <tr><td colspan="2" bgcolor="{INK}"><font color="white" point-size="16"><b>users</b></font></td></tr>
      <tr><td align="left"><b>PK</b></td><td align="left">id : INTEGER</td></tr>
      <tr><td align="left"></td><td align="left">name : VARCHAR(100)</td></tr>
      <tr><td align="left"><b>UQ</b></td><td align="left">email : VARCHAR(255)</td></tr>
      <tr><td align="left"></td><td align="left">password_hash : VARCHAR(255)</td></tr>
      <tr><td align="left"></td><td align="left">is_admin : BOOLEAN</td></tr>
      <tr><td align="left"></td><td align="left">bio : VARCHAR(280)</td></tr>
      <tr><td align="left"></td><td align="left">created_at : DATETIME</td></tr>
    </table>>];
  books [label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="7" bgcolor="white">
      <tr><td colspan="2" bgcolor="{INK}"><font color="white" point-size="16"><b>books</b></font></td></tr>
      <tr><td align="left"><b>PK</b></td><td align="left">id : INTEGER</td></tr>
      <tr><td align="left"></td><td align="left">title : VARCHAR(200)</td></tr>
      <tr><td align="left"></td><td align="left">author : VARCHAR(150)</td></tr>
      <tr><td align="left"></td><td align="left">genre : VARCHAR(80)</td></tr>
      <tr><td align="left"></td><td align="left">year : INTEGER</td></tr>
      <tr><td align="left"></td><td align="left">isbn : VARCHAR(20)</td></tr>
      <tr><td align="left"></td><td align="left">description : TEXT</td></tr>
      <tr><td align="left"></td><td align="left">cover_color : VARCHAR(7)</td></tr>
    </table>>];
  ratings [label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="7" bgcolor="white">
      <tr><td colspan="2" bgcolor="{ACCENT}"><font color="white" point-size="16"><b>ratings</b></font></td></tr>
      <tr><td align="left"><b>PK</b></td><td align="left">id : INTEGER</td></tr>
      <tr><td align="left"><b>FK</b></td><td align="left">user_id : INTEGER</td></tr>
      <tr><td align="left"><b>FK</b></td><td align="left">book_id : INTEGER</td></tr>
      <tr><td align="left"></td><td align="left">score : INTEGER (1-5)</td></tr>
      <tr><td align="left"></td><td align="left">review : TEXT</td></tr>
      <tr><td align="left"></td><td align="left">created_at : DATETIME</td></tr>
      <tr><td align="left" colspan="2"><font point-size="11">UNIQUE(user_id, book_id)</font></td></tr>
    </table>>];

  {{ rank=same; users; books }}
  users   -> ratings [taillabel="1  ", headlabel="  0..*", arrowhead=crow, dir=both, arrowtail=none];
  books   -> ratings [taillabel="1  ", headlabel="  0..*", arrowhead=crow, dir=both, arrowtail=none];
}}
'''

for name, src in [("architecture", architecture), ("class_diagram", class_diagram), ("erd", erd)]:
    dot = os.path.join(OUT, name + ".dot"); png = os.path.join(OUT, name + ".png")
    open(dot, "w").write(src)
    subprocess.run(["dot", "-Tpng", dot, "-o", png], check=True)
    from PIL import Image
    w,h = Image.open(png).size
    print(f"{name}.png {w}x{h} aspect={h/w:.3f}")
