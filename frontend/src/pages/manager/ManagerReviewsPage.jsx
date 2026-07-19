import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import { getAllReviewsRequest, replyToReviewRequest } from '../../services/managerService';
import { formatDate } from '../../utils/format';

function Stars({ n }) {
  return <span>{'★'.repeat(n)}{'☆'.repeat(5-n)}</span>;
}

export default function ManagerReviewsPage() {
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [reviews,  setReviews]  = useState([]);
  const [filter,   setFilter]   = useState('all');   // all | unanswered
  const [replyForms, setReplyForms] = useState({});  // { [reviewId]: text }
  const [saving,   setSaving]   = useState(null);
  const [search,   setSearch]   = useState('');

  async function load() {
    try { const d = await getAllReviewsRequest(); setReviews(d); }
    catch (e) { setError(e?.response?.data?.detail || 'Failed to load reviews.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function handleReply(reviewId) {
    const text = (replyForms[reviewId] || '').trim();
    if (!text) return;
    setSaving(reviewId);
    try {
      await replyToReviewRequest(reviewId, text);
      setReplyForms((f) => ({ ...f, [reviewId]: '' }));
      await load();
    } catch (e) { setError(e?.response?.data?.detail || 'Reply failed.'); }
    finally { setSaving(null); }
  }

  const filtered = reviews.filter((r) => {
    if (filter === 'unanswered' && r.has_reply) return false;
    if (search && !(
      (r.product_name||'').toLowerCase().includes(search.toLowerCase()) ||
      (r.customer_email||'').toLowerCase().includes(search.toLowerCase())
    )) return false;
    return true;
  });

  if (loading) return <Loader label="Loading reviews" />;
  if (error)   return <ErrorState message={error} />;

  const unansweredCount = reviews.filter((r) => !r.has_reply).length;

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <div>
          <h1 className="mgr-page__title">Reviews</h1>
          <p className="mgr-page__sub">{reviews.length} total · {unansweredCount} awaiting reply</p>
        </div>
      </div>
      {error && <ErrorState message={error} />}

      <div className="mgr-toolbar">
        <input className="mgr-search" placeholder="Search by product or customer…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <div className="mgr-filters">
          <button className={`mgr-filter-btn${filter==='all'?' active':''}`} onClick={() => setFilter('all')}>All</button>
          <button className={`mgr-filter-btn${filter==='unanswered'?' active':''}`} onClick={() => setFilter('unanswered')}>
            Unanswered ({unansweredCount})
          </button>
        </div>
      </div>

      <div className="reviews-mgr-list">
        {filtered.length === 0 && <p className="muted">No reviews match the filter.</p>}
        {filtered.map((r) => (
          <div key={r.id} className={`card review-mgr-card${r.has_reply ? '' : ' review-mgr-card--pending'}`}>
            <div className="review-mgr-card__head">
              <div>
                <p className="review-mgr-card__product">{r.product_name}</p>
                <p className="muted" style={{ fontSize:'0.8rem' }}>{r.customer_email} · {formatDate(r.created_at)}</p>
              </div>
              <div style={{ textAlign:'right' }}>
                <span style={{ color:'#f4b942', fontSize:'1rem' }}><Stars n={r.rating} /></span>
                {!r.has_reply && <div className="reply-needed-badge">Reply needed</div>}
              </div>
            </div>
            <p className="review-mgr-card__comment">{r.comment || <em>No comment.</em>}</p>

            {r.has_reply && (
              <div className="review-reply">
                <span className="review-reply__badge">Your Reply</span>
                <p>{r.reply_text}</p>
              </div>
            )}

            <div className="review-reply-form">
              <textarea
                className="field__control"
                rows={2}
                placeholder={r.has_reply ? 'Update reply…' : 'Write a reply…'}
                value={replyForms[r.id] || ''}
                onChange={(e) => setReplyForms((f) => ({ ...f, [r.id]: e.target.value }))}
              />
              <Button
                onClick={() => handleReply(r.id)}
                loading={saving === r.id}
                style={{ alignSelf: 'flex-end' }}
              >
                {r.has_reply ? 'Update Reply' : 'Post Reply'}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
