import { useState } from 'react'
import { createTaskComment } from '../api/comments'
import { useAuth } from '../context/AuthContext'

function Comment({ comment, projectId, taskId, onDeleted }) {
  const { user } = useAuth()
  const [showReply, setShowReply] = useState(false)

  return (
    <div className="comment">
      <div className="comment-header">
        <strong>{comment.author_name}</strong>
        <span className="comment-time">
          {new Date(comment.created_at).toLocaleString()}
        </span>
      </div>
      <p className="comment-body">{comment.body}</p>
      {!comment.parent_id && (
        <button
          className="btn-link"
          onClick={() => setShowReply((v) => !v)}
        >
          {showReply ? 'Cancel' : 'Reply'}
        </button>
      )}
      {showReply && (
        <ReplyForm
          projectId={projectId}
          taskId={taskId}
          parentId={comment.id}
          onPosted={(reply) => {
            onDeleted(reply, 'add', comment.id)
            setShowReply(false)
          }}
        />
      )}
      {comment.replies?.length > 0 && (
        <div className="comment-replies">
          {comment.replies.map((reply) => (
            <div key={reply.id} className="comment reply">
              <div className="comment-header">
                <strong>{reply.author_name}</strong>
                <span className="comment-time">
                  {new Date(reply.created_at).toLocaleString()}
                </span>
              </div>
              <p className="comment-body">{reply.body}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ReplyForm({ projectId, taskId, parentId, onPosted }) {
  const [body, setBody] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!body.trim()) return
    setLoading(true)
    try {
      const res = await createTaskComment(projectId, taskId, {
        body,
        parent_id: parentId,
      })
      setBody('')
      onPosted(res.data)
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to post reply')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="reply-form" onSubmit={handleSubmit}>
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Write a reply..."
        rows={2}
        required
      />
      <button className="btn btn-sm btn-primary" type="submit" disabled={loading}>
        {loading ? 'Posting...' : 'Post Reply'}
      </button>
    </form>
  )
}

export default function CommentBox({ comments, projectId, taskId, onCommentsChange }) {
  const [body, setBody] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!body.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await createTaskComment(projectId, taskId, { body })
      onCommentsChange([...comments, { ...res.data, replies: [] }])
      setBody('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to post comment')
    } finally {
      setLoading(false)
    }
  }

  // handle reply added inline
  const handleReplyOrDelete = (reply, action, parentId) => {
    if (action === 'add') {
      onCommentsChange(
        comments.map((c) =>
          c.id === parentId
            ? { ...c, replies: [...(c.replies || []), reply] }
            : c
        )
      )
    }
  }

  return (
    <div className="comment-section">
      <h3 className="section-title">Comments ({comments.length})</h3>

      {comments.length === 0 && (
        <p className="empty-state">No comments yet. Be the first!</p>
      )}

      {comments.map((comment) => (
        <Comment
          key={comment.id}
          comment={comment}
          projectId={projectId}
          taskId={taskId}
          onDeleted={handleReplyOrDelete}
        />
      ))}

      <form className="comment-form" onSubmit={handleSubmit}>
        <h4>Add a Comment</h4>
        {error && <div className="error-msg">{error}</div>}
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Write a comment..."
          rows={3}
          required
        />
        <button className="btn btn-primary btn-sm" type="submit" disabled={loading}>
          {loading ? 'Posting...' : 'Post Comment'}
        </button>
      </form>
    </div>
  )
}
