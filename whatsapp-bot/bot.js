// bot_leads.js - Adaptación del bot de ejemplo para calificar leads inmobiliarios
import makeWASocket, { useMultiFileAuthState } from "@whiskeysockets/baileys";
import qrcode from "qrcode-terminal";
import axios from "axios";
import * as dotenv from "dotenv";
import path from "path";
import fse from "fs-extra";

dotenv.config();

// ---------- Config ----------
const APP_NAME = process.env.APP_NAME || "LeadAgent";
const AGENT_API_URL = process.env.AGENT_API_URL || "http://localhost:8000/api/lead/analyze";
const AGENT_API_TOKEN = process.env.AGENT_API_TOKEN || ""; // opcional Bearer
const SESSION_DIR = process.env.SESSION_DIR || "session";
const AGENT_CHANNEL = process.env.AGENT_CHANNEL || "whatsapp";

// Asegura carpeta de sesión
fse.ensureDirSync(path.resolve(SESSION_DIR));

// ---------- Helpers ----------
const cleanText = (txt = "") => txt.replace(/[*#_`]+/g, "").trim();

const formatLeadSummary = (result) => {
  const {
    lead_score = "C",
    presupuesto,
    zona,
    tipo_propiedad,
    urgencia,
    razonamiento,
  } = result || {};

  const presupuestoTxt =
    presupuesto === null || typeof presupuesto === "undefined"
      ? "no especificado"
      : new Intl.NumberFormat("es-CO").format(presupuesto);

  const zonaTxt = zona || "zona no indicada";
  const tipoTxt = tipo_propiedad || "sin tipo definido";
  const urgenciaTxt = urgencia || "media";
  const razonamientoTxt = razonamiento || "Sin razonamiento";

  return (
    `🏠 Según lo que me dices, tu perfil es un lead tipo ${lead_score}.\n` +
    `💰 Presupuesto: ${presupuestoTxt}\n` +
    `📍 Zona: ${zonaTxt}\n` +
    `🏢 Tipo de propiedad: ${tipoTxt}\n` +
    `⏱️ Urgencia: ${urgenciaTxt}\n` +
    `🧠 Razonamiento: ${razonamientoTxt}`
  );
};

async function callLeadAgent(message, jid) {
  const payload = {
    mensaje: message,
    canal: AGENT_CHANNEL,
    nombre: null,
    contacto: `whatsapp:${jid}`,
  };

  const headers = { "Content-Type": "application/json" };
  if (AGENT_API_TOKEN) headers.Authorization = `Bearer ${AGENT_API_TOKEN}`;

  const response = await axios.post(AGENT_API_URL, payload, { headers, timeout: 15000 });
  return response.data;
}

// ---------- Inicializa WhatsApp ----------
const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);
const sock = makeWASocket({ auth: state });

sock.ev.on("creds.update", saveCreds);

// QR + conexión
sock.ev.on("connection.update", (update) => {
  const { qr, connection, lastDisconnect } = update;

  if (qr) {
    console.log("🔑 Escanea este código QR para conectar WhatsApp:");
    qrcode.generate(qr, { small: true });
  }

  if (connection === "open") console.log("✅ Conectado correctamente a WhatsApp");
  if (connection === "close") {
    console.error("❌ Conexión cerrada", lastDisconnect?.error?.message);
    console.log("Reinicia el bot para reconectar.");
  }
});

console.log(`🤖 ${APP_NAME} escuchando mensajes de WhatsApp...`);

// ---------- Manejo de mensajes ----------
sock.ev.on("messages.upsert", async (mUp) => {
  const m = mUp.messages?.[0];
  if (!m) return;
  if (m.key?.fromMe) return;

  const texto =
    m.message?.conversation ||
    m.message?.extendedTextMessage?.text ||
    m.message?.imageMessage?.caption ||
    "";
  if (!texto) return;

  const textoLimpio = cleanText(texto);
  const jid = m.key.remoteJid;

  console.log("📩 Mensaje de", jid, ":", textoLimpio);

  // --- Comandos simples ---
  if (textoLimpio === "!help" || textoLimpio === "!ayuda") {
    await sock.sendMessage(jid, {
      text: `🤖 Soy el bot de leads inmobiliarios.\n` +
        `Envíame tu consulta y te doy una calificación (A/B/C) con presupuesto y zona.\n` +
        `Comandos:\n` +
        `!help - esta ayuda\n` +
        `!ping - probar disponibilidad\n`,
    });
    return;
  }

  if (textoLimpio === "!ping") {
    await sock.sendMessage(jid, { text: "🏓 Pong! Estoy en línea." });
    return;
  }

  // --- Flujo principal: llamar al agente ---
  try {
    const result = await callLeadAgent(textoLimpio, jid);
    const respuesta = formatLeadSummary(result);
    await sock.sendMessage(jid, { text: respuesta });
    console.log("✅ Respuesta enviada a", jid);
  } catch (err) {
    console.error("❌ Error al llamar al agente:", err?.message || err);
    const fallback =
      "Lo siento, no pude analizar tu mensaje ahora mismo. Intenta de nuevo en unos segundos.";
    await sock.sendMessage(jid, { text: fallback });
  }
});
