<script lang="ts">
  /**
   * @copyright CEA
   * @author CEA
   * @license CECILL
   *
   * This software is a collaborative computer program whose purpose is to
   * generate and explore labeled data for computer vision applications.
   * This software is governed by the CeCILL-C license under French law and
   * abiding by the rules of distribution of free software. You can use,
   * modify and/ or redistribute the software under the terms of the CeCILL-C
   * license as circulated by CEA, CNRS and INRIA at the following URL
   *
   * http://www.cecill.info
   */

  // Imports

  import Konva from "konva";
  import { Circle } from "svelte-konva";

  import type { PolygonGroupPoint } from "../lib/types/canvas2dTypes";

  // Exports
  export let viewId: string;
  export let stage: Konva.Stage;
  export let zoomFactor: Record<string, number>;
  export let polygonId: string;
  export let points: PolygonGroupPoint[][];

  export let handlePolygonPointsClick: (i: number, viewId: string) => void | null;
  export let handlePolygonPointsDragMove: (id: number, i: number) => void | null;
  export let handlePolygonPointsDragEnd: () => void | null;

  function scaleCircleRadius(id: number, i: number, scale: number) {
    const point: Konva.Circle = stage.findOne(`#dot-${polygonId}-${i}-${id}`);

    point.scaleX(scale);
    point.scaleY(scale);
  }
</script>

{#each points as shape, i}
  {#each shape as point, pi}
    <Circle
      on:click={() => handlePolygonPointsClick?.(pi, viewId)}
      on:dragmove={() => handlePolygonPointsDragMove?.(point.id, i)}
      on:dragend={handlePolygonPointsDragEnd}
      on:mouseover={(e) => {
        e.detail.target?.attrs?.id === `dot-${polygonId}-${i}-${point.id}` &&
          scaleCircleRadius(point.id, i, 2);
      }}
      on:mouseleave={() => scaleCircleRadius(point.id, i, 1)}
      config={{
        x: point.x,
        y: point.y,
        radius: (pi === 0 ? 6 : 4) / zoomFactor[viewId],
        fill: pi === 0 ? "#781e60" : "rgb(0,128,0)",
        stroke: "white",
        strokeWidth: 1 / zoomFactor[viewId],
        id: `dot-${polygonId}-${i}-${point.id}`,
        draggable: true,
      }}
    />
  {/each}
{/each}
