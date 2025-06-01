<script>
    export let title = "Bubble Chart Overview";
    export let xAxisLabel = "Average Rating (IMDb)";
    export let legendItems = [
      { label: "No Oscar Wins", color: "#aaa" },
      { label: "Has Oscar Wins", color: "#ffd700" }
    ];
  </script>
  
  <style>
    .info-panel {
      position: absolute;
      top: 20px;
      right: 20px;
      background: rgba(255, 255, 255, 0.8);
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 16px;
      max-width: 220px;
      font-family: sans-serif;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .info-title {
      font-size: 1.1rem;
      font-weight: bold;
      margin-bottom: 8px;
      color: #333;
    }
    .legend {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .legend-item {
      display: flex;
      align-items: center;
      margin-bottom: 6px;
    }
    .swatch {
      width: 14px;
      height: 14px;
      border-radius: 3px;
      margin-right: 8px;
      border: 1px solid #999;
    }
    .axis-label {
      margin-top: 12px;
      font-size: 0.9rem;
      color: #555;
    }
  </style>
  
  <div class="info-panel">
    <div class="info-title">{title}</div>
  
    <ul class="legend">
      {#each legendItems as item}
        <li class="legend-item">
          <div class="swatch" style="background: {item.color}"></div>
          <div>{item.label}</div>
        </li>
      {/each}
    </ul>
  
    <div class="axis-label">X-axis: {xAxisLabel}</div>
  </div>
  