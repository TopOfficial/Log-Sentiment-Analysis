import { useEffect, useRef } from "react";
import { format, toZonedTime } from "date-fns-tz";
import ReactMarkdown from "react-markdown";

// TypeScript type for `messages` prop (Optional)
export type Message = {
  SentDate: string; // Timestamp
  Role: number; // 0 for LLM, 1 for User
  Content: string; // Message content
  MessageId: number | string; // Unique ID for each message
  ConversationId: number; // Conversation ID
  isLoading?: boolean; // Add this to your Message type
};

type ChatProps = {
  messages: Message[]; // An array of messages
};

const Chat = ({ messages }: ChatProps) => {
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom when new messages are added
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      ref={chatContainerRef}
      className="h-120 overflow-y-scroll border border-gray-300 rounded-md p-4 bg-gray-100"
    >
      {messages.map((message) => (
        <div
          key={`${message.ConversationId}-${message.MessageId}`}
          className={`mb-4 flex flex-col ${
            message.Role === 1 ? "items-end" : "items-start"
          }`}
        >
          <div
            className={`max-w-[70%] px-4 py-2 rounded-lg overflow-x-auto ${
              message.isLoading
                ? "bg-gray-200 text-gray-600 flex items-center gap-2" // Styling for loading bubble
                : message.Role === 1
                ? "bg-primaryGreen text-white"
                : "bg-grey text-black"
            }`}
          >
            {message.isLoading ? (
              <>
                <span>Loading...</span>
              </>
            ) : (
              <ReactMarkdown>{message.Content}</ReactMarkdown>
            )}
          </div>
          {!message.isLoading && (
            <span className="text-xs text-gray-500 mt-1">
              {format(
                toZonedTime(new Date(message.SentDate), "Asia/Bangkok"),
                "dd/MM/yyyy HH:mm"
              )}
            </span>
          )}
        </div>
      ))}
    </div>
  );
};

export default Chat;
