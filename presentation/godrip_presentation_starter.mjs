/**
 * GoDrip DBMS Project Presentation — production starter
 *
 * Install:
 *   npm install pptxgenjs jszip
 *
 * Run:
 *   node godrip_presentation_starter.mjs
 *
 * Output:
 *   GoDrip_DBMS_Project_Presentation_v2.pptx
 *
 * This starter intentionally uses only editable PowerPoint text, shapes,
 * and connectors. Replace the title-side visual with a real project
 * screenshot only if one is available.
 */

import fs from "node:fs/promises";
import path from "node:path";
import pptxgen from "pptxgenjs";
import JSZip from "jszip";

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Sourav and Riyad";
pptx.company = "GoDrip";
pptx.subject = "DBMS Project Presentation";
pptx.title = "GoDrip — Database-driven fashion commerce";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Georgia",
  bodyFontFace: "Aptos",
  lang: "en-US",
};
pptx.defineSlideMaster({
  title: "GODRIP",
  background: { color: "09090D" },
  objects: [],
  slideNumber: { x: 12.30, y: 7.08, w: 0.45, h: 0.18, color: "C9A96E", fontSize: 9, align: "right" },
});

const OUT = path.resolve("GoDrip_DBMS_Project_Presentation_v2.pptx");
const W = 13.333;
const H = 7.5;

const C = {
  bg: "09090D",
  surface: "15151C",
  surface2: "1D1D26",
  ivory: "F4F0E8",
  muted: "A8A39A",
  dim: "6F6B66",
  line: "34343E",
  gold: "C9A96E",
  goldSoft: "E8D7B4",
  blue: "79A7D8",
  green: "65B88A",
  violet: "A68BC6",
  coral: "D9796D",
  white: "FFFFFF",
};

const F = {
  display: "Georgia",
  body: "Aptos",
  mono: "Aptos Mono",
};

const DOMAIN = {
  lookup: C.blue,
  admin: C.violet,
  catalog: C.gold,
  customer: C.blue,
  inventory: C.green,
  sales: C.gold,
  feedback: C.coral,
};

function addText(slide, text, x, y, w, h, {
  fontFace = F.body,
  fontSize = 18,
  color = C.ivory,
  bold = false,
  italic = false,
  align = "left",
  valign = "top",
  margin = 0,
  breakLine = false,
  fit = "shrink",
  charSpacing = 0,
  bullet,
  transparency = 0,
} = {}) {
  slide.addText(text, {
    x, y, w, h,
    fontFace, fontSize, color, bold, italic, align, valign, margin,
    breakLine, fit, charSpacing, bullet, transparency,
    paraSpaceAfterPt: 0,
    lineSpacingMultiple: 1.0,
  });
}

function addRichText(slide, runs, x, y, w, h, options = {}) {
  slide.addText(runs, {
    x, y, w, h,
    fontFace: options.fontFace || F.body,
    fontSize: options.fontSize || 18,
    color: options.color || C.ivory,
    margin: options.margin ?? 0,
    valign: options.valign || "mid",
    align: options.align || "left",
    fit: "shrink",
  });
}

function rect(slide, x, y, w, h, {
  fill = C.surface,
  line = C.line,
  radius = 0.12,
  transparency = 0,
  lineWidth = 1,
} = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: radius,
    fill: { color: fill, transparency },
    line: line === "none"
      ? { color: fill, transparency: 100 }
      : { color: line, width: lineWidth },
  });
}

function rule(slide, x, y, w, color = C.line, width = 1) {
  slide.addShape(pptx.ShapeType.line, {
    x, y, w, h: 0,
    line: { color, width, beginArrowType: "none", endArrowType: "none" },
  });
}

function connector(slide, x1, y1, x2, y2, {
  color = C.line,
  width = 1.2,
  dash = "solid",
  endArrowType = "none",
} = {}) {
  slide.addShape(pptx.ShapeType.line, {
    x: x1,
    y: y1,
    w: x2 - x1,
    h: y2 - y1,
    line: {
      color,
      width,
      dash,
      beginArrowType: "none",
      endArrowType,
    },
  });
}

function base(slide, number, kicker, title, subtitle = "") {
  slide.background = { color: C.bg };
  const titleSize = title.length > 62 ? 25.5 : title.length > 52 ? 27 : 30;
  addText(slide, kicker.toUpperCase(), 0.72, 0.38, 4.5, 0.25, {
    fontSize: 10.5, color: C.gold, bold: true, charSpacing: 1.8,
  });
  addText(slide, title, 0.72, 0.72, 11.85, 0.63, {
    fontFace: F.display, fontSize: titleSize, color: C.ivory, bold: true,
  });
  if (subtitle) {
    addText(slide, subtitle, 0.72, 1.39, 11.65, 0.38, {
      fontSize: 15.5, color: C.muted,
    });
  }
  rule(slide, 0.72, 7.03, 11.88, C.line, 0.8);
  addText(slide, "GO DRIP  /  DBMS PROJECT", 0.72, 7.11, 3.1, 0.16, {
    fontSize: 8.7, color: C.dim, bold: true, charSpacing: 1.1,
  });
  addText(slide, String(number).padStart(2, "0"), 12.12, 7.09, 0.46, 0.17, {
    fontSize: 9.5, color: C.gold, bold: true, align: "right",
  });
}

function note(slide, text) {
  slide.addNotes(text);
}

function sectionLabel(slide, text, x, y, color = C.gold) {
  addText(slide, text.toUpperCase(), x, y, 2.8, 0.22, {
    fontSize: 10, color, bold: true, charSpacing: 1.4,
  });
}

function entity(slide, {
  x, y, w = 1.75, h = 0.70, name, keys = "", accent = C.gold,
  strong = false, fontSize = 11.3,
}) {
  rect(slide, x, y, w, h, {
    fill: strong ? C.surface2 : C.surface,
    line: accent,
    lineWidth: strong ? 1.7 : 0.9,
  });
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w: 0.055, h,
    fill: { color: accent },
    line: { color: accent, transparency: 100 },
  });
  addText(slide, name.toUpperCase(), x + 0.15, y + 0.10, w - 0.25, 0.20, {
    fontSize, color: C.ivory, bold: true,
  });
  addText(slide, keys, x + 0.15, y + 0.35, w - 0.25, h - 0.40, {
    fontSize: 8.5, color: C.muted, fontFace: F.mono,
  });
}

function cardinality(slide, text, x, y, color = C.muted) {
  addText(slide, text, x, y, 0.50, 0.18, {
    fontSize: 8.2, color, bold: true, align: "center",
  });
}

function moduleBlock(slide, {
  x, y, w, h, title, count, tables, accent,
}) {
  rect(slide, x, y, w, h, {
    fill: C.surface,
    line: C.line,
  });
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w: 0.07, h,
    fill: { color: accent },
    line: { color: accent, transparency: 100 },
  });
  addText(slide, title.toUpperCase(), x + 0.22, y + 0.18, w - 0.95, 0.25, {
    fontSize: 12.5, color: accent, bold: true, charSpacing: 0.8,
  });
  addText(slide, String(count).padStart(2, "0"), x + w - 0.62, y + 0.13, 0.40, 0.30, {
    fontFace: F.display, fontSize: 18, color: C.ivory, bold: true, align: "right",
  });
  rule(slide, x + 0.22, y + 0.53, w - 0.44, C.line, 0.7);
  addText(slide, tables, x + 0.22, y + 0.68, w - 0.44, h - 0.82, {
    fontSize: 11.5, color: C.ivory, fit: "shrink",
  });
}

function stat(slide, value, label, x, y, accent = C.gold) {
  addText(slide, value, x, y, 0.72, 0.36, {
    fontFace: F.display, fontSize: 23, color: accent, bold: true,
  });
  addText(slide, label.toUpperCase(), x + 0.75, y + 0.08, 1.55, 0.22, {
    fontSize: 9.5, color: C.muted, bold: true, charSpacing: 0.8,
  });
}

// ---------------------------------------------------------------------------
// Slide 1 — Title
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  slide.background = { color: C.bg };

  slide.addShape(pptx.ShapeType.rect, {
    x: 8.15, y: 0, w: 5.18, h: 7.5,
    fill: { color: C.surface },
    line: { color: C.surface, transparency: 100 },
  });
  for (let i = 0; i < 8; i += 1) {
    const x = 8.55 + (i % 4) * 1.10;
    const y = 0.72 + Math.floor(i / 4) * 3.25;
    rect(slide, x, y, 0.72, 2.65, {
      fill: i % 3 === 0 ? C.gold : C.surface2,
      line: i % 3 === 0 ? C.gold : C.line,
      transparency: i % 3 === 0 ? 18 : 0,
    });
  }
  connector(slide, 8.30, 3.76, 12.85, 3.76, { color: C.gold, width: 1.2 });
  addText(slide, "PRODUCT  /  VARIANT  /  STOCK  /  ORDER", 8.42, 3.84, 4.35, 0.26, {
    fontSize: 9.5, color: C.goldSoft, bold: true, charSpacing: 1.0, align: "center",
  });

  rule(slide, 0.72, 0.83, 0.72, C.gold, 2.3);
  addText(slide, "DATABASE-DRIVEN FASHION COMMERCE", 0.72, 1.05, 5.6, 0.28, {
    fontSize: 11.5, color: C.gold, bold: true, charSpacing: 1.5,
  });
  addText(slide, "GO\nDRIP", 0.68, 1.58, 6.55, 2.42, {
    fontFace: F.display, fontSize: 62, color: C.ivory, bold: true,
  });
  addText(slide,
    "A relational core for product discovery, inventory, checkout, fulfilment and feedback.",
    0.75, 4.35, 6.45, 0.78,
    { fontSize: 21, color: C.goldSoft, fit: "shrink" },
  );
  addRichText(slide, [
    { text: "SOURAV", options: { bold: true, color: C.ivory } },
    { text: "  Backend & FastAPI", options: { color: C.muted } },
    { text: "    |    ", options: { color: C.gold } },
    { text: "RIYAD", options: { bold: true, color: C.ivory } },
    { text: "  Frontend & Authentication", options: { color: C.muted } },
  ], 0.75, 5.63, 7.0, 0.34, { fontSize: 13.5 });
  addText(slide, "SHARED  /  DATABASE DESIGN + QUERY HANDLING", 0.75, 6.22, 5.65, 0.25, {
    fontSize: 10, color: C.gold, bold: true, charSpacing: 1.1,
  });
  addText(slide, "DBMS PROJECT PRESENTATION", 0.75, 7.02, 3.25, 0.18, {
    fontSize: 8.7, color: C.dim, bold: true, charSpacing: 1.0,
  });

  note(slide,
    "Good morning. We are Sourav and Riyad, and our project is GoDrip, a fashion e-commerce platform. The interface lets people shop, but the real coordination happens in the database. In seven minutes, we will show how the system connects products, variants, stock, orders, fulfilment and feedback.",
  );
}

// ---------------------------------------------------------------------------
// Slide 2 — Storyline
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 2, "Project storyline", "The project began with one consistency problem",
    "Customers and managers act differently, but both depend on the same facts.");

  // Connectors first.
  connector(slide, 2.65, 3.48, 5.05, 3.48, { color: C.gold, width: 2, endArrowType: "triangle" });
  connector(slide, 7.00, 3.48, 9.38, 2.70, { color: C.blue, width: 1.6, endArrowType: "triangle" });
  connector(slide, 7.00, 3.48, 9.38, 4.35, { color: C.green, width: 1.6, endArrowType: "triangle" });

  sectionLabel(slide, "The friction", 0.85, 2.05, C.coral);
  addText(slide, "Scattered facts", 0.85, 2.43, 2.55, 0.46, {
    fontFace: F.display, fontSize: 24, bold: true,
  });
  addText(slide,
    "A product page can look correct while stock, order status or customer data is already inconsistent.",
    0.85, 3.08, 2.55, 1.05,
    { fontSize: 16.5, color: C.muted },
  );
  addText(slide, "The issue is coordination—not only interface design.", 0.85, 4.62, 2.65, 0.76, {
    fontSize: 17.5, color: C.coral, bold: true,
  });

  rect(slide, 4.10, 2.35, 2.90, 2.30, { fill: C.surface2, line: C.gold, lineWidth: 1.4 });
  addText(slide, "ONE\nRELATIONAL\nCORE", 4.42, 2.71, 2.28, 1.15, {
    fontFace: F.display, fontSize: 26, color: C.goldSoft, bold: true, align: "center", valign: "mid",
  });
  addText(slide, "identity • catalog • stock • sales", 4.38, 4.10, 2.35, 0.26, {
    fontSize: 10.5, color: C.muted, align: "center",
  });

  sectionLabel(slide, "Customer journey", 9.35, 2.02, C.blue);
  addText(slide, "Discover → choose variant → cart → checkout → track → review",
    9.35, 2.41, 3.10, 0.78, { fontSize: 16.5, color: C.ivory, bold: true });

  sectionLabel(slide, "Manager journey", 9.35, 3.77, C.green);
  addText(slide, "Control catalog → manage stock → fulfil orders → monitor outcomes",
    9.35, 4.16, 3.10, 0.82, { fontSize: 16.5, color: C.ivory, bold: true });

  rule(slide, 0.85, 5.86, 11.55, C.line, 0.8);
  addText(slide, "GoDrip converts separate retail actions into one traceable data story.",
    1.40, 6.09, 10.45, 0.45, {
      fontFace: F.display, fontSize: 23, color: C.goldSoft, bold: true, align: "center",
    });

  note(slide,
    "We started with one problem: consistency. Customers need the right item, size, color, price and availability. Managers need reliable product, stock, order and fulfilment information. If those facts are stored separately or repeated, the interface can show conflicting answers. GoDrip therefore uses one relational core to support two journeys: a customer journey from discovery to review, and a manager journey from catalog control to operational reporting.",
  );
}

// ---------------------------------------------------------------------------
// Slide 3 — Architecture
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 3, "System architecture", "Each layer owns one responsibility",
    "A thin client, protected API and relational data layer keep the system understandable.");

  const xs = [0.82, 3.12, 5.60, 8.16, 10.63];
  const widths = [1.65, 1.90, 1.95, 1.85, 1.85];
  const centers = xs.map((x, i) => x + widths[i] / 2);
  for (let i = 0; i < centers.length - 1; i += 1) {
    connector(slide, centers[i] + widths[i] / 2 - 0.18, 3.40,
      centers[i + 1] - widths[i + 1] / 2 + 0.18, 3.40,
      { color: C.gold, width: 1.7, endArrowType: "triangle" });
  }

  const layers = [
    ["CUSTOMER +\nMANAGER", "Two route trees", C.blue],
    ["REACT + VITE", "Router • Axios • Context", C.gold],
    ["FASTAPI", "Routers • Pydantic • CRUD", C.violet],
    ["SQLALCHEMY", "ORM • sessions • Alembic", C.green],
    ["POSTGRESQL", "Supabase-hosted data", C.gold],
  ];
  layers.forEach(([name, sub, accent], i) => {
    rect(slide, xs[i], 2.67, widths[i], 1.45, {
      fill: C.surface,
      line: accent,
      lineWidth: i === 2 ? 1.8 : 1.0,
    });
    addText(slide, name, xs[i] + 0.14, 2.92, widths[i] - 0.28, 0.48, {
      fontFace: F.display, fontSize: 16, color: C.ivory, bold: true, align: "center", valign: "mid",
    });
    addText(slide, sub, xs[i] + 0.12, 3.58, widths[i] - 0.24, 0.25, {
      fontSize: 9.2, color: C.muted, align: "center",
    });
  });

  connector(slide, 6.56, 2.60, 6.56, 1.97, { color: C.blue, width: 1.4, endArrowType: "triangle" });
  rect(slide, 5.43, 1.83, 2.28, 0.55, { fill: C.surface2, line: C.blue });
  addText(slide, "SUPABASE AUTH / JWT", 5.58, 2.00, 1.98, 0.20, {
    fontSize: 10.2, color: C.blue, bold: true, align: "center",
  });

  connector(slide, 6.56, 4.18, 6.56, 4.82, { color: C.violet, width: 1.4, endArrowType: "triangle" });
  rect(slide, 5.43, 4.83, 2.28, 0.55, { fill: C.surface2, line: C.violet });
  addText(slide, "STATIC PRODUCT MEDIA", 5.58, 5.00, 1.98, 0.20, {
    fontSize: 10.2, color: C.violet, bold: true, align: "center",
  });

  const annotations = [
    ["VITE PROXY", "/api + /static", C.gold],
    ["BEARER JWT", "Axios interceptor", C.blue],
    ["RBAC", "is_admin + require_admin", C.green],
    ["MIDDLEWARE", "CORS + GZip", C.violet],
  ];
  annotations.forEach(([t, b, accent], i) => {
    const x = 1.12 + i * 3.0;
    sectionLabel(slide, t, x, 5.78, accent);
    addText(slide, b, x, 6.08, 2.55, 0.28, { fontSize: 13.5, color: C.ivory, bold: true });
  });

  note(slide,
    "The architecture separates responsibility. React and Vite handle the customer and manager interfaces. Axios attaches the bearer token and calls FastAPI. FastAPI validates requests with Pydantic, applies authentication and role checks, and delegates data access through CRUD and SQLAlchemy. PostgreSQL stores the relational facts. Supabase Auth provides identity and JWT validation, while FastAPI also serves product media. This separation makes each layer easier to test, replace and debug.",
  );
}

// ---------------------------------------------------------------------------
// Slide 4 — Schema landscape
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 4, "Complete schema landscape",
    "Forty-five tables stay understandable because the schema is modular",
    "The target model is grouped by business responsibility—not by implementation file.");

  const blocks = [
    {
      title: "Lookup + administration", count: 10, accent: C.violet,
      tables: "genders • colors • sizes • materials • seasons\nroles • permissions • role_permissions • admins • activity_logs",
    },
    {
      title: "Catalog + product", count: 10, accent: C.gold,
      tables: "brands • suppliers • categories • subcategories • collections\nproducts • product_images • product_variants • product_specifications • product_collections",
    },
    {
      title: "Customer", count: 8, accent: C.blue,
      tables: "customers • customer_profiles • customer_addresses • wishlists • wishlist_items • carts • cart_items • customer_notifications",
    },
    {
      title: "Warehouse + inventory", count: 3, accent: C.green,
      tables: "warehouses • inventory • inventory_movements",
    },
    {
      title: "Sales + fulfilment", count: 11, accent: C.gold,
      tables: "shipping_methods • coupons • coupon_usages • orders • order_items • order_status_history • payments • shipments • invoices • return_requests • refunds",
    },
    {
      title: "Feedback", count: 3, accent: C.coral,
      tables: "reviews • review_images • review_replies",
    },
  ];

  const positions = [
    [0.72, 2.00, 3.83, 1.72],
    [4.75, 2.00, 3.83, 1.72],
    [8.78, 2.00, 3.83, 1.72],
    [0.72, 3.97, 3.83, 1.49],
    [4.75, 3.97, 3.83, 1.49],
    [8.78, 3.97, 3.83, 1.49],
  ];
  blocks.forEach((block, i) => moduleBlock(slide, {
    x: positions[i][0], y: positions[i][1], w: positions[i][2], h: positions[i][3], ...block,
  }));

  rule(slide, 0.72, 5.77, 11.88, C.line, 0.8);
  stat(slide, "45", "tables", 0.95, 6.02, C.ivory);
  stat(slide, "65", "indexes", 3.18, 6.02, C.blue);
  stat(slide, "12", "functions", 5.45, 6.02, C.violet);
  stat(slide, "11", "triggers", 7.82, 6.02, C.green);
  stat(slide, "17", "views", 10.12, 6.02, C.gold);

  addText(slide,
    "IMPLEMENTATION STATUS  /  45-table PostgreSQL target; 10 ORM-mapped core tables currently active in the API.",
    0.90, 6.62, 11.55, 0.22,
    { fontSize: 9.7, color: C.coral, bold: true, charSpacing: 0.35, align: "center" },
  );

  note(slide,
    "The full target schema contains forty-five tables, but it remains understandable because each table has one business responsibility. Lookup and administration define controlled values and permissions. Catalog and product tables describe what is sold. Customer tables support identity and shopping state. Inventory tables locate and audit stock. Sales tables preserve the order lifecycle, and feedback closes the loop. The migrations also define sixty-five indexes, twelve functions, eleven triggers and seventeen views. Importantly, the active API currently maps only a ten-table core; the full target is the next deployment stage.",
  );
}

// ---------------------------------------------------------------------------
// Slide 5 — ER A: Catalog and inventory
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 5, "E–R model / catalog + inventory",
    "A sellable item is a variant, and stock belongs to a location",
    "The design separates descriptive product facts from SKU-level and warehouse-level facts.");

  // Connectors first, then boxes.
  connector(slide, 2.33, 2.15, 4.65, 2.92, { color: C.gold, width: 1.0 });
  connector(slide, 2.33, 3.20, 4.65, 3.10, { color: C.gold, width: 1.0 });
  connector(slide, 2.33, 4.28, 4.65, 3.26, { color: C.blue, width: 1.0 });
  connector(slide, 2.33, 5.35, 3.30, 5.35, { color: C.gold, width: 1.0 });
  connector(slide, 4.90, 5.35, 5.40, 3.55, { color: C.gold, width: 1.0 });

  connector(slide, 6.60, 3.16, 7.15, 2.22, { color: C.gold, width: 1.0 });
  connector(slide, 6.60, 3.16, 9.37, 2.22, { color: C.gold, width: 1.0 });
  connector(slide, 6.60, 3.16, 7.15, 4.26, { color: C.gold, width: 1.6 });
  connector(slide, 3.15, 4.25, 7.15, 4.52, { color: C.blue, width: 1.0 });
  connector(slide, 8.95, 4.61, 9.48, 4.61, { color: C.green, width: 1.8 });
  connector(slide, 11.28, 4.61, 11.72, 5.62, { color: C.green, width: 1.0 });
  connector(slide, 10.38, 5.60, 10.38, 4.95, { color: C.green, width: 1.0 });
  connector(slide, 3.85, 2.15, 3.85, 1.70, { color: C.violet, width: 0.9 });
  connector(slide, 3.85, 2.15, 4.65, 3.02, { color: C.violet, width: 0.9 });

  entity(slide, { x: 0.75, y: 1.80, w: 1.58, name: "brands", keys: "PK id\nUK name, slug", accent: C.gold });
  entity(slide, { x: 0.75, y: 2.85, w: 1.58, name: "suppliers", keys: "PK id\nUK contact_email", accent: C.gold });
  entity(slide, { x: 0.75, y: 3.93, w: 1.58, name: "genders", keys: "PK id\nUK name", accent: C.blue });
  entity(slide, { x: 0.75, y: 5.00, w: 1.58, name: "categories", keys: "PK id\nUK slug", accent: C.gold });
  entity(slide, { x: 3.30, y: 5.00, w: 1.60, name: "subcategories", keys: "PK id\nFK category_id", accent: C.gold });

  entity(slide, {
    x: 4.65, y: 2.70, w: 1.95, h: 0.90, name: "products",
    keys: "PK id\nFK brand • supplier • subcategory • collection • gender",
    accent: C.gold, strong: true, fontSize: 13,
  });
  entity(slide, { x: 7.15, y: 1.82, w: 1.80, name: "product_images", keys: "PK id\nFK product_id", accent: C.gold });
  entity(slide, { x: 9.37, y: 1.82, w: 2.02, name: "product_specifications", keys: "PK id\nUK product_id + spec_key", accent: C.gold });

  entity(slide, {
    x: 7.15, y: 4.10, w: 1.80, h: 1.02, name: "product_variants",
    keys: "PK id\nFK product • color • size • material\nUK sku • barcode",
    accent: C.gold, strong: true, fontSize: 12.2,
  });
  entity(slide, { x: 1.35, y: 3.90, w: 1.80, name: "color • size • material", keys: "lookup PKs\n1:M to variants", accent: C.blue });

  entity(slide, {
    x: 9.48, y: 4.10, w: 1.80, h: 1.02, name: "inventory",
    keys: "PK id\nUK variant_id + warehouse_id\ngenerated available_stock",
    accent: C.green, strong: true, fontSize: 12.2,
  });
  entity(slide, { x: 9.48, y: 5.52, w: 1.80, name: "warehouses", keys: "PK id\nUK code", accent: C.green });
  entity(slide, { x: 11.20, y: 5.52, w: 1.35, name: "movements", keys: "FK inventory_id\nappend-only", accent: C.green, fontSize: 10.2 });

  entity(slide, { x: 3.05, y: 1.20, w: 1.60, name: "collections", keys: "PK id\nFK season_id", accent: C.violet });
  entity(slide, { x: 3.05, y: 1.85, w: 1.60, name: "product_collections", keys: "PK product_id + collection_id", accent: C.violet, fontSize: 9.7 });

  cardinality(slide, "1:M", 2.62, 2.36, C.gold);
  cardinality(slide, "1:M", 6.68, 3.84, C.gold);
  cardinality(slide, "M:M", 8.98, 4.44, C.green);
  cardinality(slide, "1:M", 11.20, 5.20, C.green);

  addText(slide,
    "PRODUCT  →  VARIANT  →  INVENTORY  →  MOVEMENT",
    5.05, 6.35, 7.15, 0.34,
    { fontSize: 14, color: C.goldSoft, bold: true, charSpacing: 0.9, align: "center" },
  );

  note(slide,
    "This ER view explains the most important catalog decision. A product stores shared information such as name, brand, supplier and category. A product variant represents the actual purchasable SKU, with one color, size and material. Inventory then records that variant at a specific warehouse, so stock is never attached vaguely to the product. The generated available-stock value prevents derived-data inconsistency, while inventory movements form an audit ledger. Product collections and lookup tables resolve the remaining many-to-many and controlled-value relationships.",
  );
}

// ---------------------------------------------------------------------------
// Slide 6 — ER B: Customer and order lifecycle
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 6, "E–R model / customer + sales",
    "The order is the transactional hub of the customer journey",
    "Identity, shopping state, payment, delivery, return and feedback remain connected without duplication.");

  // Central path and secondary connectors first.
  connector(slide, 2.35, 3.65, 3.15, 3.65, { color: C.gold, width: 2.0, endArrowType: "triangle" });
  connector(slide, 5.02, 3.65, 5.55, 3.65, { color: C.gold, width: 2.0, endArrowType: "triangle" });
  connector(slide, 7.47, 3.65, 8.02, 3.65, { color: C.gold, width: 2.0, endArrowType: "triangle" });

  connector(slide, 1.53, 3.28, 1.53, 2.25, { color: C.blue, width: 1.0 });
  connector(slide, 1.53, 4.02, 1.53, 5.10, { color: C.blue, width: 1.0 });
  connector(slide, 2.35, 3.45, 3.08, 2.06, { color: C.blue, width: 1.0 });
  connector(slide, 2.35, 3.60, 3.08, 2.88, { color: C.blue, width: 1.0 });
  connector(slide, 4.72, 2.06, 8.02, 3.46, { color: C.blue, width: 0.9 });
  connector(slide, 4.72, 2.88, 8.02, 3.55, { color: C.blue, width: 0.9 });

  connector(slide, 4.08, 4.10, 4.08, 5.15, { color: C.gold, width: 0.9 });
  connector(slide, 4.65, 4.10, 6.35, 5.15, { color: C.gold, width: 0.9 });
  connector(slide, 4.95, 3.95, 8.26, 2.23, { color: C.gold, width: 0.9 });
  connector(slide, 4.95, 3.84, 10.20, 2.23, { color: C.gold, width: 0.9 });
  connector(slide, 4.95, 3.73, 10.20, 3.32, { color: C.gold, width: 0.9 });

  connector(slide, 4.95, 3.96, 10.18, 4.65, { color: C.coral, width: 1.1 });
  connector(slide, 11.82, 4.65, 12.22, 4.65, { color: C.coral, width: 1.0 });
  connector(slide, 7.47, 3.93, 8.25, 5.85, { color: C.coral, width: 1.0 });
  connector(slide, 9.95, 5.85, 10.30, 5.85, { color: C.coral, width: 0.9 });

  entity(slide, {
    x: 0.72, y: 3.28, w: 1.63, h: 0.74, name: "customers",
    keys: "PK id\nUK email", accent: C.blue, strong: true, fontSize: 12.5,
  });
  entity(slide, { x: 0.72, y: 1.55, w: 1.63, name: "customer_profiles", keys: "PK/FK customer_id\nUK phone", accent: C.blue, fontSize: 10.3 });
  entity(slide, { x: 0.72, y: 5.10, w: 1.63, name: "addresses", keys: "PK id\nFK customer_id", accent: C.blue });

  entity(slide, { x: 3.08, y: 1.70, w: 1.64, name: "cart + items", keys: "customer 1:1 cart\nvariant 1:M items", accent: C.blue });
  entity(slide, { x: 3.08, y: 2.52, w: 1.64, name: "wishlist + items", keys: "customer 1:1 list\nvariant 1:M items", accent: C.blue, fontSize: 10.4 });

  entity(slide, {
    x: 3.15, y: 3.25, w: 1.87, h: 0.85, name: "orders",
    keys: "PK id • UK order_number\nFK customer • addresses • ship method • coupon",
    accent: C.gold, strong: true, fontSize: 13,
  });
  entity(slide, {
    x: 5.55, y: 3.25, w: 1.92, h: 0.85, name: "order_items",
    keys: "PK id\nFK order_id • variant_id\ngenerated line_total",
    accent: C.gold, strong: true, fontSize: 12.3,
  });
  entity(slide, {
    x: 8.02, y: 3.25, w: 1.80, h: 0.85, name: "product_variants",
    keys: "PK id\nUK sku • barcode",
    accent: C.gold, strong: true, fontSize: 11.5,
  });

  entity(slide, { x: 3.15, y: 5.15, w: 1.87, name: "status_history", keys: "FK order_id\nFK changed_by admin", accent: C.gold });
  entity(slide, { x: 5.55, y: 5.15, w: 1.92, name: "coupon_usages", keys: "FK coupon • customer • order", accent: C.gold });

  entity(slide, { x: 8.26, y: 1.58, w: 1.64, name: "payments", keys: "FK/UK order_id\nUK transaction_ref", accent: C.gold });
  entity(slide, { x: 10.20, y: 1.58, w: 1.64, name: "shipments", keys: "FK/UK order_id\nUK tracking_number", accent: C.green });
  entity(slide, { x: 10.20, y: 2.67, w: 1.64, name: "invoices", keys: "FK/UK order_id\nUK invoice_number", accent: C.gold });

  entity(slide, { x: 10.18, y: 4.30, w: 1.64, name: "return_requests", keys: "FK order • customer\nFK approved_by admin", accent: C.coral, fontSize: 10.2 });
  entity(slide, { x: 12.00, y: 4.30, w: 0.98, name: "refunds", keys: "FK/UK return_id", accent: C.coral, fontSize: 9.5 });
  entity(slide, { x: 8.25, y: 5.50, w: 1.70, name: "reviews", keys: "FK customer • variant • order", accent: C.coral });
  entity(slide, { x: 10.30, y: 5.50, w: 1.76, name: "review media + reply", keys: "images 1:M\nreply 1:1 + admin", accent: C.coral, fontSize: 9.8 });

  cardinality(slide, "1:M", 2.52, 3.43, C.gold);
  cardinality(slide, "1:M", 5.04, 3.43, C.gold);
  cardinality(slide, "M:1", 7.50, 3.43, C.gold);
  cardinality(slide, "1:1", 8.25, 2.83, C.gold);
  cardinality(slide, "1:M", 7.65, 5.53, C.coral);

  addText(slide,
    "CUSTOMER  →  ORDER  →  ORDER ITEM  →  VARIANT",
    2.60, 6.45, 6.85, 0.26,
    { fontSize: 13.5, color: C.goldSoft, bold: true, charSpacing: 0.75, align: "center" },
  );

  note(slide,
    "The customer and sales model is centered on the order. A customer owns a profile, addresses, cart and wishlist, then places many orders. Each order contains line items, and every line item points to the exact purchased variant. Payment, shipment and invoice use one-to-one order links. Status history preserves change over time, while return requests and refunds continue the transaction without overwriting it. Reviews link customer, order and variant, which supports verified feedback. This structure keeps the journey connected while avoiding repeated customer, product or fulfilment data.",
  );
}

// ---------------------------------------------------------------------------
// Slide 7 — Normalization and design quality
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 7, "Relational design goodness",
    "Normalization removes anomalies; constraints keep the model trustworthy",
    "Good design is not the number of tables—it is the reason each fact has one correct home.");

  const x0 = 0.76;
  const gap = 0.18;
  const bw = 2.86;
  const items = [
    ["1NF", "Atomic values", "Lookup and junction tables replace arrays, comma-separated values and repeating groups.", C.blue],
    ["2NF", "Variant-level facts", "Product facts stay in products; SKU, color, size and material stay in product_variants.", C.gold],
    ["3NF", "No transitive facts", "Auth/profile, brand, supplier, category and address details live in their own relations.", C.violet],
    ["BCNF", "Determinants are keys", "Composite junction keys and unique SKU, barcode and warehouse-stock keys enforce candidate keys.", C.green],
  ];
  items.forEach(([nf, heading, body, accent], i) => {
    const x = x0 + i * (bw + gap);
    addText(slide, nf, x, 2.04, bw, 0.48, {
      fontFace: F.display, fontSize: 28, color: accent, bold: true,
    });
    rule(slide, x, 2.58, bw, accent, 1.2);
    addText(slide, heading, x, 2.82, bw, 0.36, {
      fontSize: 17, color: C.ivory, bold: true,
    });
    addText(slide, body, x, 3.34, bw, 1.18, {
      fontSize: 15, color: C.muted,
    });
  });

  addText(slide, "ANTI-PATTERN", 0.78, 4.95, 1.55, 0.22, {
    fontSize: 9.8, color: C.coral, bold: true, charSpacing: 1.1,
  });
  addText(slide, "products(id, name, colors[], sizes[], stock)", 0.78, 5.30, 4.25, 0.32, {
    fontFace: F.mono, fontSize: 14, color: C.coral, bold: true,
  });
  connector(slide, 5.15, 5.44, 6.10, 5.44, { color: C.gold, width: 1.8, endArrowType: "triangle" });
  addText(slide, "NORMALIZED", 6.28, 4.95, 1.55, 0.22, {
    fontSize: 9.8, color: C.green, bold: true, charSpacing: 1.1,
  });
  addText(slide, "products  →  product_variants  →  inventory", 6.28, 5.30, 5.55, 0.32, {
    fontFace: F.mono, fontSize: 14, color: C.green, bold: true,
  });

  rect(slide, 0.78, 6.00, 11.80, 0.61, { fill: C.surface2, line: C.line });
  addText(slide,
    "INTEGRITY BEYOND NORMALIZATION  /  PK + FK + UNIQUE + CHECK  •  generated stock and line totals  •  audit ledgers  •  triggers  •  indexed views",
    1.00, 6.20, 11.35, 0.20,
    { fontSize: 10.2, color: C.goldSoft, bold: true, charSpacing: 0.28, align: "center" },
  );

  note(slide,
    "The design is good because each business fact has one correct home. First normal form keeps values atomic through lookup and junction tables. Second normal form separates general products from purchasable variants and warehouse stock. Third normal form removes transitive facts such as brand, supplier, profile and address details. BCNF is supported through composite keys and alternate keys such as SKU, barcode and variant-plus-warehouse. Integrity continues beyond normalization: generated columns prevent derived-data anomalies, constraints reject invalid states, ledgers preserve history, and indexes and views keep queries practical.",
  );
}

// ---------------------------------------------------------------------------
// Slide 8 — Tools and techniques
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 8, "Tools and techniques",
    "The stack mirrors the separation in the data model",
    "Each technology solves one layer of the same transaction.");

  const layers = [
    ["01", "FRONTEND", "React 18 • Vite • Router v6 • Axios • Context API", "Reusable components, two route trees, route guards, token interceptor", C.blue],
    ["02", "BACKEND", "FastAPI • Pydantic v2 • SQLAlchemy 2 • Alembic", "Routers, schemas, CRUD layer, validation, CORS, GZip, StaticFiles", C.violet],
    ["03", "AUTH + DATA", "Supabase Auth • JWT • PostgreSQL", "Token validation, auto-provisioned customer row, RBAC manager access", C.green],
    ["04", "DATABASE ENGINEERING", "ER modelling • 3NF/BCNF • SQL migrations", "Constraints, indexes, functions, triggers, views, seed and query library", C.gold],
  ];

  layers.forEach(([num, label, stack, technique, accent], i) => {
    const y = 1.97 + i * 1.13;
    addText(slide, num, 0.82, y + 0.13, 0.62, 0.38, {
      fontFace: F.display, fontSize: 22, color: accent, bold: true,
    });
    rule(slide, 1.58, y + 0.34, 0.72, accent, 1.2);
    addText(slide, label, 2.50, y + 0.08, 2.20, 0.25, {
      fontSize: 11.5, color: accent, bold: true, charSpacing: 0.9,
    });
    addText(slide, stack, 2.50, y + 0.40, 4.20, 0.30, {
      fontSize: 17, color: C.ivory, bold: true,
    });
    addText(slide, technique, 7.15, y + 0.18, 5.00, 0.52, {
      fontSize: 14.3, color: C.muted,
    });
    if (i < layers.length - 1) rule(slide, 2.50, y + 0.93, 9.65, C.line, 0.6);
  });

  rect(slide, 0.82, 6.58, 11.55, 0.30, { fill: C.surface2, line: C.line });
  addText(slide, "TECHNIQUE  /  service boundaries in code match entity boundaries in the database",
    1.05, 6.66, 11.10, 0.16,
    { fontSize: 9.2, color: C.goldSoft, bold: true, charSpacing: 0.55, align: "center" });

  note(slide,
    "The technology stack follows the same separation. React, Router, Axios and Context manage the user experience. FastAPI, Pydantic and SQLAlchemy handle API contracts, validation and data access. Supabase provides authentication and hosted PostgreSQL, while JWT validation and role dependencies protect manager actions. At database level, ER modelling and normalization define the structure, then migrations, constraints, indexes, functions, triggers, views and seed data turn that structure into an operational system.",
  );
}

// ---------------------------------------------------------------------------
// Slide 9 — Contributions and learning
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 9, "Team contribution + learning",
    "We divided implementation ownership and shared the data work",
    "Clear responsibility accelerated development; shared database decisions kept the system coherent.");

  sectionLabel(slide, "Sourav", 0.85, 2.00, C.violet);
  addText(slide, "BACKEND OWNER", 0.85, 2.38, 3.35, 0.30, {
    fontFace: F.display, fontSize: 22, color: C.ivory, bold: true,
  });
  addText(slide,
    "FastAPI architecture\nRouters, CRUD and query handling\nSQLAlchemy / database integration\nValidation and protected endpoints",
    0.85, 2.98, 3.65, 1.95,
    { fontSize: 16, color: C.muted },
  );

  sectionLabel(slide, "Shared", 5.12, 2.00, C.gold);
  rect(slide, 4.90, 2.32, 3.45, 2.77, { fill: C.surface2, line: C.gold, lineWidth: 1.4 });
  addText(slide, "DATABASE\nDESIGN", 5.25, 2.70, 2.75, 0.82, {
    fontFace: F.display, fontSize: 25, color: C.goldSoft, bold: true, align: "center", valign: "mid",
  });
  addText(slide, "Normalization decisions\nQuery handling\nIntegration testing + debugging",
    5.25, 3.72, 2.75, 0.98,
    { fontSize: 15, color: C.ivory, bold: true, align: "center" });

  sectionLabel(slide, "Riyad", 9.05, 2.00, C.blue);
  addText(slide, "FRONTEND OWNER", 9.05, 2.38, 3.35, 0.30, {
    fontFace: F.display, fontSize: 22, color: C.ivory, bold: true,
  });
  addText(slide,
    "React interface implementation\nCustomer and manager route trees\nAuthentication flows and route guards\nFrontend service / API integration",
    9.05, 2.98, 3.55, 1.95,
    { fontSize: 16, color: C.muted },
  );

  rule(slide, 0.85, 5.42, 11.55, C.line, 0.8);
  addText(slide, "WHAT WE LEARNED", 0.85, 5.67, 1.80, 0.23, {
    fontSize: 10, color: C.gold, bold: true, charSpacing: 1.2,
  });
  addText(slide,
    "requirements → entities + keys     •     protected React ↔ FastAPI flow     •     Supabase identity ↔ relational profile     •     normalization ↔ performance     •     schema ↔ API debugging",
    0.85, 6.10, 11.55, 0.47,
    { fontSize: 13.3, color: C.ivory, bold: true, align: "center" },
  );

  note(slide,
    "We divided ownership by layer. I, Sourav, focused on FastAPI, routers, CRUD and query handling, SQLAlchemy integration, validation and protected backend endpoints. Riyad focused on the React interface, customer and manager routes, authentication flows, route guards and frontend service integration. We both worked on database design and query handling, then tested the integration together. The project taught us how to translate business requirements into keys and relationships, connect protected frontend and backend flows, integrate Supabase identity, balance normalization with performance, and debug schema-to-API mismatches.",
  );
}

// ---------------------------------------------------------------------------
// Slide 10 — Limitations and roadmap
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 10, "Limitations + future plan",
    "The next milestone is one deployable source of truth",
    "The prototype proves the workflow; production readiness now depends on schema alignment.");

  sectionLabel(slide, "Current limitations", 0.82, 2.00, C.coral);
  const limits = [
    "45-table target is not fully mapped by the active 10-model API",
    "Extended catalog, inventory, coupon, return and analytics routers remain disabled",
    "No production payment gateway or courier integration",
    "Limited automated testing, monitoring, backup and deployment",
    "localStorage token strategy has an XSS security tradeoff",
  ];
  limits.forEach((t, i) => {
    const y = 2.45 + i * 0.70;
    addText(slide, String(i + 1).padStart(2, "0"), 0.83, y, 0.42, 0.22, {
      fontFace: F.display, fontSize: 13, color: C.coral, bold: true,
    });
    addText(slide, t, 1.42, y - 0.02, 4.72, 0.48, {
      fontSize: 14.8, color: C.ivory,
    });
  });

  connector(slide, 6.42, 2.12, 6.42, 5.92, { color: C.line, width: 1.0 });
  connector(slide, 6.62, 5.78, 7.26, 5.78, { color: C.gold, width: 1.8, endArrowType: "triangle" });

  sectionLabel(slide, "Ordered roadmap", 7.18, 2.00, C.green);
  const roadmap = [
    ["01", "Unify SQL migrations, Alembic, ORM models and API schemas"],
    ["02", "Map and enable the remaining domain routers"],
    ["03", "Integrate real payment, courier and secure-session flows"],
    ["04", "Add tests, CI/CD, load checks, monitoring and backups"],
    ["05", "Add full-text search, recommendations and richer analytics"],
  ];
  roadmap.forEach(([n, t], i) => {
    const y = 2.43 + i * 0.70;
    addText(slide, n, 7.18, y, 0.42, 0.24, {
      fontFace: F.display, fontSize: 13, color: C.green, bold: true,
    });
    addText(slide, t, 7.77, y - 0.02, 4.62, 0.48, {
      fontSize: 14.8, color: C.ivory,
    });
  });

  rule(slide, 0.82, 6.12, 11.58, C.gold, 1.2);
  addText(slide,
    "The database is not behind GoDrip—it is the coordination layer that makes the product work.",
    1.08, 6.34, 11.05, 0.42,
    { fontFace: F.display, fontSize: 21, color: C.goldSoft, bold: true, align: "center" },
  );

  note(slide,
    "The strongest limitation is also our clearest roadmap. The repository contains a complete forty-five-table target, but the active ORM and API still use a ten-table core, so some extended routers are disabled. Production payments, delivery integration, stronger session handling, testing and monitoring also remain future work. Our first priority is one canonical schema aligned across migrations, models and routes. Then we can safely enable the remaining modules, add integrations and testing, and build smarter search and analytics. The database is not behind GoDrip; it is the coordination layer that makes the product work.",
  );
}

// ---------------------------------------------------------------------------
// Appendix A — Complete table dictionary
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 11, "Appendix A", "Complete 45-table dictionary",
    "Reference view for questions; all tables are grouped by responsibility.");

  const groups = [
    ["LOOKUP / 5", "genders\ncolors\nsizes\nmaterials\nseasons", C.blue],
    ["ADMIN / 5", "roles\npermissions\nrole_permissions\nadmins\nactivity_logs", C.violet],
    ["CATALOG / 5", "brands\nsuppliers\ncategories\nsubcategories\ncollections", C.gold],
    ["CUSTOMER / 8", "customers\ncustomer_profiles\ncustomer_addresses\nwishlists\nwishlist_items\ncarts\ncart_items\ncustomer_notifications", C.blue],
    ["PRODUCT / 5", "products\nproduct_images\nproduct_variants\nproduct_specifications\nproduct_collections", C.gold],
    ["INVENTORY / 3", "warehouses\ninventory\ninventory_movements", C.green],
    ["SALES / 6", "shipping_methods\ncoupons\ncoupon_usages\norders\norder_items\norder_status_history", C.gold],
    ["FULFILMENT / 5", "payments\nshipments\ninvoices\nreturn_requests\nrefunds", C.green],
    ["FEEDBACK / 3", "reviews\nreview_images\nreview_replies", C.coral],
  ];
  groups.forEach(([title, body, accent], i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.72 + col * 4.05;
    const y = 1.98 + row * 1.60;
    rect(slide, x, y, 3.78, 1.35, { fill: C.surface, line: C.line });
    sectionLabel(slide, title, x + 0.20, y + 0.18, accent);
    addText(slide, body, x + 0.20, y + 0.52, 3.35, 0.68, {
      fontFace: F.mono, fontSize: 10.7, color: C.ivory,
    });
  });
  note(slide, "Appendix reference: complete list of the forty-five target tables grouped by module.");
}

// ---------------------------------------------------------------------------
// Appendix B — Functions, triggers, views
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 12, "Appendix B", "Database automation makes the schema operational",
    "Functions calculate, triggers protect state, and views package repeatable reporting logic.");

  const cols = [
    {
      x: 0.72, w: 3.75, accent: C.violet, title: "12 FUNCTIONS",
      body: "calculate_order_total\nget_customer_lifetime_value\nget_available_stock\nget_product_average_rating\nget_best_selling_products\nget_monthly_revenue\ncalculate_stock_valuation\nvalidate_coupon\ncalculate_shipment_eta\ncheck_return_eligibility\ngenerate_order_number\ngenerate_invoice_number",
    },
    {
      x: 4.79, w: 3.75, accent: C.green, title: "11 TRIGGERS",
      body: "generate order number\nlog order-status change\ndeduct inventory\nreserve inventory\nrestore stock on cancellation\nrestore stock on return\nprevent negative inventory\nauto-create invoice\nincrement coupon usage\nprevent duplicate review\ninitialize cart + wishlist",
    },
    {
      x: 8.86, w: 3.75, accent: C.gold, title: "17 VIEWS",
      body: "available products • best sellers\ncustomer order history • top rated\ninventory status • low stock\nrevenue by brand • category\nmonthly sales • warehouse inventory\ncustomer lifetime value\ncoupon performance • return analysis\nsupplier performance\n\nMATERIALIZED\nproduct sales • daily revenue • inventory health",
    },
  ];
  cols.forEach(({ x, w, accent, title, body }) => {
    rule(slide, x, 2.00, w, accent, 2);
    addText(slide, title, x, 2.23, w, 0.32, {
      fontFace: F.display, fontSize: 20, color: accent, bold: true,
    });
    addText(slide, body, x, 2.82, w, 3.62, {
      fontFace: F.mono, fontSize: 11.2, color: C.ivory,
    });
  });
  note(slide, "Appendix reference: the target database includes twelve functions, eleven triggers and seventeen views, including three materialized views.");
}

// ---------------------------------------------------------------------------
// Appendix C — Target vs active implementation
// ---------------------------------------------------------------------------
{
  const slide = pptx.addSlide("GODRIP");
  base(slide, 13, "Appendix C", "The repository contains a target model and an active core",
    "This distinction explains why some domain routers exist in code but are not yet enabled.");

  connector(slide, 4.25, 3.75, 5.10, 3.75, { color: C.gold, width: 1.8, endArrowType: "triangle" });
  connector(slide, 8.22, 3.75, 9.05, 3.75, { color: C.green, width: 1.8, endArrowType: "triangle" });

  rect(slide, 0.78, 2.25, 3.47, 3.20, { fill: C.surface, line: C.gold, lineWidth: 1.3 });
  sectionLabel(slide, "Target design", 1.08, 2.58, C.gold);
  addText(slide, "45 TABLES", 1.08, 3.02, 2.90, 0.50, {
    fontFace: F.display, fontSize: 28, color: C.ivory, bold: true,
  });
  addText(slide, "Normalized PostgreSQL schema\nMigrations, constraints and automation\nFull domain coverage",
    1.08, 3.78, 2.75, 1.10, { fontSize: 15, color: C.muted });

  rect(slide, 5.10, 2.25, 3.12, 3.20, { fill: C.surface2, line: C.coral, lineWidth: 1.3 });
  sectionLabel(slide, "Active API core", 5.40, 2.58, C.coral);
  addText(slide, "10 MODELS", 5.40, 3.02, 2.55, 0.50, {
    fontFace: F.display, fontSize: 28, color: C.ivory, bold: true,
  });
  addText(slide,
    "customers • categories • suppliers\nproducts • orders • order_items\npayments • shipments • reviews • cart_items",
    5.40, 3.78, 2.48, 1.15,
    { fontFace: F.mono, fontSize: 10.6, color: C.muted },
  );

  rect(slide, 9.05, 2.25, 3.52, 3.20, { fill: C.surface, line: C.green, lineWidth: 1.3 });
  sectionLabel(slide, "Next deployment", 9.35, 2.58, C.green);
  addText(slide, "ONE SCHEMA", 9.35, 3.02, 2.88, 0.50, {
    fontFace: F.display, fontSize: 28, color: C.ivory, bold: true,
  });
  addText(slide,
    "Align SQL + Alembic + ORM\nMap remaining domain models\nEnable routers and integration tests",
    9.35, 3.78, 2.82, 1.10,
    { fontSize: 15, color: C.muted },
  );

  addText(slide,
    "Honest status reporting strengthens the project: the design is complete, while implementation remains incremental.",
    1.15, 6.16, 11.05, 0.40,
    { fontFace: F.display, fontSize: 19.5, color: C.goldSoft, bold: true, align: "center" },
  );
  note(slide, "Appendix reference: comparison between the forty-five-table normalized target and the ten-model active API core.");
}

async function addFadeTransitions(filePath) {
  const input = await fs.readFile(filePath);
  const zip = await JSZip.loadAsync(input);
  const transition = '<p:transition spd="med" advClick="1"><p:fade/></p:transition>';
  const slideFiles = Object.keys(zip.files)
    .filter((name) => /^ppt\/slides\/slide\d+\.xml$/.test(name));

  for (const name of slideFiles) {
    let xml = await zip.file(name).async("string");
    if (xml.includes("<p:transition")) continue;
    if (xml.includes("<p:timing")) {
      xml = xml.replace("<p:timing", `${transition}<p:timing`);
    } else if (xml.includes("<p:extLst")) {
      xml = xml.replace("<p:extLst", `${transition}<p:extLst`);
    } else {
      xml = xml.replace("</p:sld>", `${transition}</p:sld>`);
    }
    zip.file(name, xml);
  }

  const output = await zip.generateAsync({
    type: "nodebuffer",
    compression: "DEFLATE",
  });
  await fs.writeFile(filePath, output);
}

await pptx.writeFile({ fileName: OUT, compression: true });
await addFadeTransitions(OUT);
console.log(`Created ${OUT}`);
