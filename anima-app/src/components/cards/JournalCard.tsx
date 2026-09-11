import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Feather, X, ListBullets, TextHTwo, Moon, Trash } from '@phosphor-icons/react';
import { addJournalEntry, deleteJournalEntry, getJournal } from '../../lib/api';

interface Entry { id: string; html: string; text: string; is_dream: boolean; tags: string[]; ts: number; }

const fmtDate = (ts: number) =>
  new Date(ts * 1000).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });

function RichEditor({ onHtml, onText }: { onHtml: (h: string) => void; onText: (t: string) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const emit = () => {
    const el = ref.current; if (!el) return;
    onHtml(el.innerHTML); onText(el.innerText);
  };
  const cmd = (c: string, v?: string) => { document.execCommand(c, false, v); ref.current?.focus(); emit(); };
  const Tool = ({ onClick, children, label }: any) => (
    <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={onClick} aria-label={label}
      className="grid h-8 w-8 place-items-center rounded-lg text-muted transition-colors hover:bg-surface-2 hover:text-lantern">
      {children}
    </button>
  );
  return (
    <div className="rounded-2xl border border-line bg-bg">
      <div className="flex items-center gap-1 border-b border-line px-2 py-1.5">
        <Tool label="Bold" onClick={() => cmd('bold')}><span className="font-bold text-[15px] leading-none">B</span></Tool>
        <Tool label="Italic" onClick={() => cmd('italic')}><span className="font-serif italic text-[15px] leading-none">I</span></Tool>
        <Tool label="List" onClick={() => cmd('insertUnorderedList')}><ListBullets size={16} /></Tool>
        <Tool label="Heading" onClick={() => cmd('formatBlock', 'H2')}><TextHTwo size={16} /></Tool>
      </div>
      <div ref={ref} contentEditable suppressContentEditableWarning onInput={emit}
        className="min-h-[160px] px-4 py-3 text-[15px] leading-relaxed text-ink outline-none [&_h2]:font-wizard [&_h2]:text-lg empty:before:content-[attr(data-ph)] empty:before:text-faint"
        data-ph="Write freely, from the heart. No one reads this but you…"
        style={{ backgroundImage: 'repeating-linear-gradient(transparent, transparent 27px, color-mix(in srgb, var(--line) 50%, transparent) 28px)' }}
      />
    </div>
  );
}

export function JournalCard() {
  const [open, setOpen] = useState(false);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [html, setHtml] = useState('');
  const [text, setText] = useState('');
  const [dream, setDream] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editorKey, setEditorKey] = useState(0);

  const load = () => getJournal().then((d) => setEntries(d?.entries || [])).catch(() => {});
  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!text.trim()) return;
    setSaving(true);
    try { await addJournalEntry({ html, text, is_dream: dream }); setHtml(''); setText(''); setDream(false); setEditorKey((k) => k + 1); load(); }
    finally { setSaving(false); }
  };
  const remove = async (id: string) => { await deleteJournalEntry(id); load(); };

  const last = entries[0];

  return (
    <>
      {/* the card on the page */}
      <motion.button type="button" onClick={() => setOpen(true)} whileHover={{ y: -3 }}
        className="group relative w-full overflow-hidden rounded-card border border-line bg-surface p-5 text-left transition-colors hover:border-lantern/30"
        style={{ backgroundImage: 'repeating-linear-gradient(transparent, transparent 23px, color-mix(in srgb, var(--line) 35%, transparent) 24px), radial-gradient(100% 80% at 0% 0%, color-mix(in srgb, var(--lantern) 8%, transparent), transparent 60%)' }}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-full"
              style={{ backgroundColor: 'color-mix(in srgb, var(--lantern) 14%, transparent)' }}>
              <Feather size={21} weight="light" className="text-lantern" />
            </span>
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-faint">journal & dreams</p>
              <p className="font-wizard text-lg leading-tight">Write freely, from the heart</p>
            </div>
          </div>
          <span className="shrink-0 rounded-full border border-line px-2.5 py-1 text-[11px] text-faint">
            {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
          </span>
        </div>

        {last ? (
          <div className="mt-3.5">
            <p className="line-clamp-2 font-wizard text-[15px] leading-relaxed text-muted">{last.text || '(a drawing, a list, a quiet page)'}</p>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              {last.is_dream && <span className="rounded-full bg-mood-anxious/15 px-2 py-0.5 text-[10px] font-medium text-mood-anxious">dream</span>}
              {last.tags.map((t) => (
                <span key={t} className="rounded-full border border-line px-2 py-0.5 text-[10px] text-faint">{t}</span>
              ))}
              <span className="ml-auto text-[10px] text-faint">{fmtDate(last.ts)}</span>
            </div>
          </div>
        ) : (
          <p className="mt-3 text-[13px] leading-relaxed text-faint">
            A page that’s only yours — thoughts, gratitude, or a dream you don’t want to lose. The wizard quietly tags the dreams.
          </p>
        )}
      </motion.button>

      {/* the editor overlay */}
      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 overflow-y-auto bg-bg">
            <div className="pointer-events-none fixed inset-0"
              style={{ background: 'radial-gradient(120% 70% at 50% -10%, color-mix(in srgb, var(--lantern) 12%, transparent), transparent 60%)' }} />
            <div className="relative mx-auto max-w-md px-5 pb-12 pt-6">
              <div className="flex items-center justify-between">
                <button onClick={() => setOpen(false)} className="flex items-center gap-1.5 text-sm text-faint transition-colors hover:text-lantern">
                  <X size={18} weight="light" /> close
                </button>
                <button onClick={() => setDream((d) => !d)}
                  className="flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[12px] transition-all"
                  style={{
                    borderColor: dream ? 'var(--mood-anxious)' : 'var(--line)',
                    color: dream ? 'var(--mood-anxious)' : 'var(--muted)',
                    backgroundColor: dream ? 'color-mix(in srgb, var(--mood-anxious) 12%, transparent)' : 'transparent',
                  }}>
                  <Moon size={14} weight={dream ? 'fill' : 'light'} /> this is a dream
                </button>
              </div>

              <h2 className="mt-5 font-wizard text-[28px] leading-tight">Your journal</h2>
              <p className="mt-1 text-sm text-muted">Only you read this. Write the way you think.</p>

              <div className="mt-5"><RichEditor key={editorKey} onHtml={setHtml} onText={setText} /></div>

              <button onClick={save} disabled={!text.trim() || saving}
                className="mt-3 w-full rounded-full bg-lantern py-3 text-sm font-medium text-bg transition-all hover:bg-ember hover:shadow-[0_0_22px_rgba(224,162,58,0.4)] disabled:opacity-40">
                {saving ? 'Saving…' : dream ? 'Save & let the wizard read the dream' : 'Save entry'}
              </button>

              <div className="mt-8 space-y-3">
                {entries.length === 0 && <p className="text-center text-sm text-faint">Nothing written yet. The page is patient.</p>}
                {entries.map((e) => (
                  <motion.div key={e.id} layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    className="rounded-card border border-line bg-surface p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex flex-wrap items-center gap-1.5">
                        {e.is_dream && <span className="rounded-full bg-mood-anxious/15 px-2 py-0.5 text-[10px] font-medium text-mood-anxious">dream</span>}
                        {e.tags.map((t) => <span key={t} className="rounded-full border border-line px-2 py-0.5 text-[10px] text-faint">{t}</span>)}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-faint">{fmtDate(e.ts)}</span>
                        <button onClick={() => remove(e.id)} aria-label="Delete"
                          className="text-faint transition-colors hover:text-mood-angry"><Trash size={14} weight="light" /></button>
                      </div>
                    </div>
                    <div className="prose-motif text-[15px] leading-relaxed text-ink"
                      dangerouslySetInnerHTML={{ __html: e.html || `<p>${e.text}</p>` }} />
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
