import React, { useState, useEffect, useRef } from 'react';
import api from '../api/client';
import {
  Bot,
  Send,
  User,
  Sparkles,
  FileText,
  AlertCircle,
  HelpCircle,
  RefreshCw,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Cpu
} from 'lucide-react';

interface ChatMessage {
  id: number;
  sender: 'user' | 'assistant';
  message: string;
  evidence_references?: Array<{
    document_name: string;
    page_number: number;
    citation: string;
  }>;
  created_at?: string;
}

export const AssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchingHistory, setFetchingHistory] = useState(true);
  const [llmEngine, setLlmEngine] = useState<string>('EvidenceRAG Grounding Engine');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchHistory = async () => {
    try {
      const res = await api.get('/assistant/history');
      if (res.data?.messages && res.data.messages.length > 0) {
        setMessages(res.data.messages);
      } else {
        // Welcome initial message
        setMessages([
          {
            id: 0,
            sender: 'assistant',
            message:
              "Hello! I am your EvidenceRAG Document Assistant. I analyze your uploaded certificates and verified issues to explain statutory compliance, missing fields, or cross-document discrepancies. What would you like to verify today?",
            evidence_references: []
          }
        ]);
      }
    } catch (err) {
      console.error('Error fetching chat history:', err);
    } finally {
      setFetchingHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || inputText;
    if (!textToSend.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now(),
      sender: 'user',
      message: textToSend.trim()
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!customText) setInputText('');
    setLoading(true);

    try {
      const res = await api.post('/assistant/chat', { message: textToSend.trim() });
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        message: res.data.message,
        evidence_references: res.data.evidence_references || []
      };
      setLlmEngine(res.data.model_name || 'EvidenceRAG Grounding Engine');
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        message:
          'Unable to process your query at this moment. Please check your document verification dashboard or re-try your question.',
        evidence_references: []
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = [
    'Why is my income certificate flagged?',
    'Which mandatory fields are missing across my documents?',
    'Explain my verification report',
    'What should I correct before submitting my application?'
  ];

  return (
    <div className="space-y-4 max-w-4xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#CBD5E1] pb-3">
        <div>
          <div className="flex items-center gap-2">
            <Bot className="h-6 w-6 text-[#2563EB]" />
            <h1 className="text-xl font-bold tracking-tight text-[#0F172A]">Ask Your Document AI Assistant</h1>
          </div>
          <p className="text-xs text-[#475569]">
            Ask questions about your uploaded credentials, detected defects, and statutory requirements. Scoped strictly to your documents.
          </p>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] text-[#475569] bg-white px-3 py-1 rounded-lg border border-[#CBD5E1]">
          <Cpu className="h-3.5 w-3.5 text-purple-600" />
          <span>Active Engine: <b className="text-[#0F172A]">{llmEngine}</b></span>
        </div>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 overflow-y-auto rounded-2xl border border-[#CBD5E1] bg-white p-4 space-y-4 shadow-xs">
        {fetchingHistory ? (
          <div className="flex h-full items-center justify-center text-xs text-[#475569]">
            <RefreshCw className="h-5 w-5 animate-spin text-[#2563EB] mr-2" />
            Loading your conversation context...
          </div>
        ) : (
          messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3 ${
                m.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              {/* Avatar */}
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl font-bold text-xs shadow-xs ${
                  m.sender === 'user'
                    ? 'bg-[#2563EB] text-white'
                    : 'bg-gradient-to-tr from-[#1D4ED8] to-[#7C3AED] text-white'
                }`}
              >
                {m.sender === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[80%] rounded-2xl p-4 text-xs leading-relaxed shadow-xs ${
                  m.sender === 'user'
                    ? 'bg-[#2563EB] text-white rounded-tr-none'
                    : 'bg-[#F8FAFF] text-[#0F172A] border border-blue-100 rounded-tl-none'
                }`}
              >
                <div className="whitespace-pre-wrap">{m.message}</div>

                {/* Evidence Citations Badges */}
                {m.evidence_references && m.evidence_references.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-blue-200/60 space-y-1">
                    <span className="text-[10px] font-bold text-[#1D4ED8] uppercase tracking-wider block">
                      Cited Document Evidence:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {m.evidence_references.map((ref, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1 rounded bg-white px-2 py-0.5 text-[10px] font-medium text-[#0F172A] border border-blue-200 shadow-xs"
                        >
                          <FileText className="h-3 w-3 text-[#2563EB]" />
                          {ref.citation || `${ref.document_name} (Page ${ref.page_number})`}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompt Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        <span className="text-[11px] font-semibold text-[#475569] shrink-0">Try asking:</span>
        {samplePrompts.map((p, i) => (
          <button
            key={i}
            onClick={() => handleSendMessage(p)}
            className="rounded-full border border-blue-200 bg-blue-50/70 px-3 py-1 text-[11px] font-medium text-[#2563EB] hover:bg-blue-100 whitespace-nowrap cursor-pointer transition-colors"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="flex items-center gap-2 rounded-2xl border border-[#CBD5E1] bg-white p-2 shadow-xs"
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask a question about your uploaded documents or verification report..."
          disabled={loading}
          className="flex-1 bg-transparent px-3 py-2 text-xs text-[#0F172A] placeholder:text-[#475569]/60 focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading || !inputText.trim()}
          className="flex items-center gap-1.5 rounded-xl bg-[#2563EB] px-4 py-2 text-xs font-semibold text-white shadow hover:bg-[#1D4ED8] disabled:opacity-50 cursor-pointer transition-colors"
        >
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <>
              <Send className="h-4 w-4" /> Send
            </>
          )}
        </button>
      </form>
    </div>
  );
};
