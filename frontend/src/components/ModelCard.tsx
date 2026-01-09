import { useState } from 'react';
import type { ModelPricing } from '../types/pricing';

interface ModelCardProps {
  model: ModelPricing;
  index: number;
}

const providerColors: Record<string, string> = {
  aws_bedrock: 'var(--aws-color)',
  openai: 'var(--openai-color)',
  anthropic: 'var(--anthropic-color)',
  google: 'var(--google-color)',
  azure: 'var(--azure-color)',
  openrouter: 'var(--openrouter-color)',
};

const providerDisplayNames: Record<string, string> = {
  aws_bedrock: 'AWS Bedrock',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google',
  azure: 'Azure',
  openrouter: 'OpenRouter',
};

const capabilityIcons: Record<string, string> = {
  text: '📝',
  vision: '🖼️',
  audio: '🎧',
  embedding: '📊',
};

function formatPrice(price: number | null): string {
  if (price === null) return '-';
  if (price === 0) return 'Free';
  return '$' + price.toFixed(2);
}

function formatNumber(num: number | null): string {
  if (num === null) return '-';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(0) + 'K';
  return num.toString();
}

export function ModelCard({ model, index }: ModelCardProps) {
  const [expanded, setExpanded] = useState(false);
  const hasExtendedPricing =
    model.pricing.cached_input !== null ||
    model.pricing.cached_write !== null ||
    model.pricing.reasoning !== null ||
    model.batch_pricing !== null;

  return (
    <article
      className="model-card"
      style={{
        animationDelay: `${index * 0.05}s`,
        '--provider-color': providerColors[model.provider] || 'var(--accent-cyan)',
      } as React.CSSProperties}
    >
      <div className="card-header">
        <div className="provider-badge">
          <span>{providerDisplayNames[model.provider] || model.provider}</span>
        </div>
        <div className="card-badges">
          <span className="capability-icons">
            {model.capabilities.map((cap) => (
              <span key={cap} title={cap}>
                {capabilityIcons[cap] || ''}
              </span>
            ))}
          </span>
          {model.context_length && (
            <span className="context-badge mono">
              {formatNumber(model.context_length)} ctx
            </span>
          )}
        </div>
      </div>

      <h2 className="model-name">{model.model_name}</h2>

      <div className="pricing">
        <div className="price-item">
          <span className="price-label">输入</span>
          <span className="price-value mono">
            {formatPrice(model.pricing.input)}
            {model.pricing.input !== null && model.pricing.input > 0 && (
              <span className="price-unit">/M</span>
            )}
          </span>
        </div>
        <div className="price-divider"></div>
        <div className="price-item">
          <span className="price-label">输出</span>
          <span className="price-value mono">
            {formatPrice(model.pricing.output)}
            {model.pricing.output !== null && model.pricing.output > 0 && (
              <span className="price-unit">/M</span>
            )}
          </span>
        </div>
      </div>

      {/* Extended pricing (expandable) */}
      {hasExtendedPricing && (
        <>
          <button
            className="expand-btn"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? '收起详情 ▲' : '更多价格 ▼'}
          </button>

          {expanded && (
            <div className="extended-pricing">
              {model.pricing.cached_input !== null && (
                <div className="ext-price-row">
                  <span>缓存读取</span>
                  <span className="mono">{formatPrice(model.pricing.cached_input)}/M</span>
                </div>
              )}
              {model.pricing.cached_write !== null && (
                <div className="ext-price-row">
                  <span>缓存写入</span>
                  <span className="mono">{formatPrice(model.pricing.cached_write)}/M</span>
                </div>
              )}
              {model.pricing.reasoning !== null && (
                <div className="ext-price-row">
                  <span>推理</span>
                  <span className="mono">{formatPrice(model.pricing.reasoning)}/M</span>
                </div>
              )}
              {model.batch_pricing && (
                <>
                  <div className="ext-price-row batch">
                    <span>批量输入</span>
                    <span className="mono">{formatPrice(model.batch_pricing.input)}/M</span>
                  </div>
                  <div className="ext-price-row batch">
                    <span>批量输出</span>
                    <span className="mono">{formatPrice(model.batch_pricing.output)}/M</span>
                  </div>
                </>
              )}
            </div>
          )}
        </>
      )}

      {/* Price bar visualization */}
      <div className="price-bar-container">
        <div
          className="price-bar input-bar"
          style={{
            width: `${Math.min(((model.pricing.input || 0) / 20) * 100, 100)}%`,
          }}
        ></div>
        <div
          className="price-bar output-bar"
          style={{
            width: `${Math.min(((model.pricing.output || 0) / 80) * 100, 100)}%`,
          }}
        ></div>
      </div>
    </article>
  );
}
