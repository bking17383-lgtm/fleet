/**
 * Fleet gdoc → plain .md auto-export
 * One-time setup (Brian, ~10 min):
 *   1. script.google.com → New project
 *   2. Paste this file → Save
 *   3. Run setup() once → authorize Drive
 *   4. Triggers → Add → exportStaleGdocs → Time-driven → Every 15 minutes
 *
 * Manifest: MyDrive/gl/gdoc_export_manifest.json
 * Log:      MyDrive/gl/export_log.txt
 */

const MANIFEST_NAME = 'gdoc_export_manifest.json';
const MANIFEST_FOLDER = 'gl';
const LOG_NAME = 'export_log.txt';

function setup() {
  exportStaleGdocs();
}

function exportStaleGdocs() {
  const manifest = loadManifest_();
  if (!manifest || !manifest.entries) {
    log_('FAIL: manifest missing or empty');
    return;
  }

  let done = 0;
  let skipped = 0;
  let failed = 0;

  manifest.entries.forEach(function (entry) {
    try {
      const result = exportOne_(entry);
      if (result === 'exported') done++;
      else if (result === 'skipped') skipped++;
      else failed++;
    } catch (e) {
      log_('FAIL ' + entry.id + ': ' + e.message);
      failed++;
    }
  });

  log_('run done=' + done + ' skipped=' + skipped + ' failed=' + failed);
}

function exportOne_(entry) {
  const sourceName = entry.source_gdoc;
  const targetPath = entry.target_md; // e.g. lester/foo.md

  const sourceFile = findFileByName_(sourceName);
  if (!sourceFile) {
    log_('MISS source: ' + sourceName);
    return 'fail';
  }

  const mime = sourceFile.getMimeType();
  if (mime !== 'application/vnd.google-apps.document') {
    log_('SKIP not a Google Doc: ' + sourceName + ' (' + mime + ')');
    return 'fail';
  }

  const targetFile = findFileByPath_(targetPath);
  const sourceUpdated = sourceFile.getLastUpdated().getTime();

  if (targetFile) {
    const targetUpdated = targetFile.getLastUpdated().getTime();
    // md is master for instructions_for_ai — skip if target newer
    if (entry.id === 'instructions_for_ai' && targetUpdated >= sourceUpdated) {
      log_('SKIP md-master newer: ' + targetPath);
      return 'skipped';
    }
    if (targetUpdated >= sourceUpdated) {
      log_('SKIP up-to-date: ' + targetPath);
      return 'skipped';
    }
  }

  const doc = DocumentApp.openById(sourceFile.getId());
  const body = doc.getBody().getText();

  const header = [
    '# Auto-exported from Google Doc',
    '**Source:** `' + sourceName + '`',
    '**Exported:** ' + new Date().toISOString(),
    '**By:** Apps Script auto-export',
    '',
    '---',
    ''
  ].join('\n');

  const content = header + body;
  writeTarget_(targetPath, content);
  log_('OK ' + entry.id + ' → ' + targetPath);
  return 'exported';
}

function loadManifest_() {
  const folder = findFolderByName_(MANIFEST_FOLDER);
  if (!folder) throw new Error('folder gl/ not found on Drive');
  const files = folder.getFilesByName(MANIFEST_NAME);
  if (!files.hasNext()) throw new Error(MANIFEST_NAME + ' not found');
  return JSON.parse(files.next().getBlob().getDataAsString());
}

function findFileByName_(name) {
  const iter = DriveApp.getFilesByName(name);
  while (iter.hasNext()) {
    const f = iter.next();
    if (f.getMimeType() === 'application/vnd.google-apps.document') return f;
  }
  return null;
}

function findFolderByName_(name) {
  const iter = DriveApp.getFoldersByName(name);
  return iter.hasNext() ? iter.next() : null;
}

function findFileByPath_(path) {
  const parts = path.split('/');
  const fileName = parts.pop();
  let folder = DriveApp.getRootFolder();
  for (let i = 0; i < parts.length; i++) {
    const sub = folder.getFoldersByName(parts[i]);
    if (!sub.hasNext()) return null;
    folder = sub.next();
  }
  const files = folder.getFilesByName(fileName);
  return files.hasNext() ? files.next() : null;
}

function writeTarget_(path, content) {
  const parts = path.split('/');
  const fileName = parts.pop();
  let folder = DriveApp.getRootFolder();
  for (let i = 0; i < parts.length; i++) {
    const sub = folder.getFoldersByName(parts[i]);
    if (!sub.hasNext()) folder = folder.createFolder(parts[i]);
    else folder = sub.next();
  }
  const existing = folder.getFilesByName(fileName);
  if (existing.hasNext()) {
    existing.next().setContent(content);
  } else {
    folder.createFile(fileName, content, MimeType.PLAIN_TEXT);
  }
}

function log_(line) {
  const ts = new Date().toISOString();
  const msg = ts + ' ' + line + '\n';
  const folder = findFolderByName_(MANIFEST_FOLDER) || DriveApp.getRootFolder();
  const files = folder.getFilesByName(LOG_NAME);
  if (files.hasNext()) {
    const f = files.next();
    f.setContent(f.getBlob().getDataAsString() + msg);
  } else {
    folder.createFile(LOG_NAME, msg, MimeType.PLAIN_TEXT);
  }
}
