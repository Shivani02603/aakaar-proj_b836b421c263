import React from 'react';
import classNames from 'classnames';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ role, content, sources }) => {
  const [copiedSource, setCopiedSource] = useState<string | null>(null);

  const handleSourceCopy = (source: string) => {
    navigator.clipboard.writeText(source).then(() => {
      setCopiedSource(source);
      setTimeout(() => setCopiedSource(null), 2000);
    });
  };

  return (
    <div className={classNames('flex', { 'justify-end': role === 'user', 'justify-start': role === 'assistant' })}>
      <div
        className={classNames(
          'max-w-lg p-4 rounded-lg shadow-md',
          {
            'bg-blue-500 text-white': role === 'user',
            'bg-gray-200 text-gray-800': role === 'assistant',
          }
        )}
      >
        <ReactMarkdown className="prose">{content}</ReactMarkdown>
        {role === 'assistant' && sources && sources.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {sources.map((source, index) => (
              <button
                key={index}
                onClick={() => handleSourceCopy(source)}
                className="text-xs bg-gray-300 text-gray-700 px-2 py-1 rounded-full hover:bg-gray-400 focus:outline-none"
              >
                {copiedSource === source ? 'Copied!' : `Source ${index + 1}`}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;