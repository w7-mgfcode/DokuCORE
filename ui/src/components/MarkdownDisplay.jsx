import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { Paper } from '@mui/material';

/**
 * Component for rendering markdown content with syntax highlighting and GitHub flavor
 */
const MarkdownDisplay = ({ content }) => {
  return (
    <Paper elevation={0} sx={{ p: 2, backgroundColor: 'transparent' }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={vscDarkPlus}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          // Customize other markdown elements as needed
          h1: ({ node, ...props }) => (
            <h1 style={{ borderBottom: '1px solid #eaeaea', paddingBottom: '0.3em' }} {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 style={{ borderBottom: '1px solid #eaeaea', paddingBottom: '0.3em' }} {...props} />
          ),
          a: ({ node, ...props }) => (
            <a style={{ color: '#0366d6', textDecoration: 'none' }} {...props} />
          ),
          img: ({ node, ...props }) => (
            <img style={{ maxWidth: '100%' }} {...props} />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote
              style={{
                borderLeft: '4px solid #dfe2e5',
                paddingLeft: '1em',
                color: '#6a737d',
                margin: '0 0 16px',
              }}
              {...props}
            />
          ),
          table: ({ node, ...props }) => (
            <div style={{ overflowX: 'auto' }}>
              <table
                style={{
                  borderCollapse: 'collapse',
                  width: '100%',
                  marginBottom: '16px',
                }}
                {...props}
              />
            </div>
          ),
          th: ({ node, ...props }) => (
            <th
              style={{
                padding: '6px 13px',
                border: '1px solid #dfe2e5',
                backgroundColor: '#f6f8fa',
                fontWeight: '600',
                textAlign: 'left',
              }}
              {...props}
            />
          ),
          td: ({ node, ...props }) => (
            <td
              style={{
                padding: '6px 13px',
                border: '1px solid #dfe2e5',
              }}
              {...props}
            />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </Paper>
  );
};

export default MarkdownDisplay;