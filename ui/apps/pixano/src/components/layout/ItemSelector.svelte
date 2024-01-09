<script lang="ts">
  /// <reference types="svelte" />
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
  import { afterUpdate, beforeUpdate } from "svelte";

  import { goto } from "$app/navigation";
  import type { DatasetInfo, DatasetItem } from "@pixano/core/src";
  import { api } from "@pixano/core";

  export let currentDatasetName: string;
  export let currentItemId: string;
  export let onClose: () => {};

  import { datasetsStore, datasetTableStore } from "$lib/stores/datasetStores";

  let currentDataset: DatasetInfo | undefined;
  datasetsStore.subscribe((value) => {
    currentDataset = value.find((dataset) => dataset.name === currentDatasetName);
  });

  let displayedItems: {
    currentItemId: string;
    lowPage: number;
    highPage: number;
    content: [
      {
        page: number;
        items: DatasetItem[];
      },
    ];
  };

  async function loadPreviousPage(): Promise<boolean> {
    if (currentDataset && displayedItems.lowPage > 1) {
      displayedItems.lowPage = displayedItems.lowPage - 1;
      const new_dbImages = await api.getDatasetItems(currentDataset.id, displayedItems.lowPage);
      if (new_dbImages) {
        displayedItems.content.unshift({
          page: displayedItems.lowPage,
          items: new_dbImages.items,
        });
        return true;
      }
    }
    return false;
  }

  async function loadNextPage(): Promise<boolean> {
    if (
      currentDataset &&
      currentDataset.page &&
      currentDataset.page.pages &&
      displayedItems.highPage < currentDataset.page.pages
    ) {
      displayedItems.highPage = displayedItems.highPage + 1;
      const new_dbImages = await api.getDatasetItems(currentDataset.id, displayedItems.highPage);
      if (new_dbImages) {
        displayedItems.content.push({
          page: displayedItems.highPage,
          items: new_dbImages.items,
        });
        return true;
      }
    }
    return false;
  }

  const goToItem = async (gotoItem: DatasetItem) => {
    if (currentDataset && currentDataset.page && currentDataset.page.page) {
      //if goto another page, change currentDataset accordingly
      let newPage = currentDataset.page.page;
      let newItems = currentDataset.page.items;
      if (
        displayedItems.content.find((page) =>
          page.items.some((item) => {
            if (item.id === gotoItem.id) {
              newPage = page.page;
              newItems = page.items;
              return true;
            }
            return false;
          }),
        )
      ) {
        datasetTableStore.update((value) => ({ ...value, currentPage: newPage }));
        currentDataset.page.page = newPage;
        currentDataset.page.items = newItems;
      }
      await goto(`/${currentDataset.name}/dataset/${gotoItem.id}?page=${newPage}`);
      onClose();
    }
  };

  let notLoading = true; //to prevent excessive pages load on scroll event
  async function handleDatasetScroll(event: Event) {
    if (notLoading) {
      notLoading = false;
      const datasetTab = event.currentTarget as Element;
      const totalContentWidth = datasetTab.scrollWidth - datasetTab.clientWidth;
      const offset10percent = Math.ceil(totalContentWidth * 0.1);
      if (datasetTab.scrollLeft < offset10percent) {
        loadPreviousPage().then((changed) => {
          if (changed) {
            //force redraw
            displayedItems = displayedItems;
          }
        });
      }
      if (datasetTab.scrollLeft > totalContentWidth - offset10percent) {
        loadNextPage().then((changed) => {
          if (changed) {
            //force redraw
            displayedItems = displayedItems;
          }
        });
      }
      setTimeout(() => {
        notLoading = true;
      }, 100);
    }
  }

  let toCenter = false;
  afterUpdate(() => {
    if (toCenter) {
      const currentElem = document.querySelector("#current") as Element;
      currentElem.scrollIntoView({ inline: "center" });
      toCenter = false;
    }
  });

  let firstUpdate = true; //before update is called two times by svelte, we prevent that
  beforeUpdate(async () => {
    if (firstUpdate) {
      if (currentDataset && currentDataset.page && currentDataset.page.page) {
        displayedItems = {
          currentItemId: currentItemId,
          lowPage: currentDataset.page.page,
          highPage: currentDataset.page.page,
          content: [
            {
              page: currentDataset.page.page,
              items: Object.values(currentDataset.page.items),
            },
          ],
        };
        firstUpdate = false;
        //to prevent weird behaviour, we will preload previous and next page, if any
        await loadPreviousPage();
        await loadNextPage();
        //curiously, we need both scrollIntoView (afterUpdate and this)
        //even if afterUpdate is called last and should be sufficient
        toCenter = true;
        const currentElem = document.querySelector("#current") as Element;
        currentElem.scrollIntoView({ inline: "center" });
      }
    }
  });
</script>

<div class="w-full fixed z-40 bg-slate-800">
  <div class="flex p-4 w-full flew-col justify-center">
    <div class="flex overflow-x-auto" on:scroll={handleDatasetScroll}>
      {#each displayedItems.content as page}
        {#each page.items as item}
          <button
            id={item.id == currentItemId ? "current" : ""}
            class="flex p-1 flex-col rounded h-min transition-colors {item.id == currentItemId
              ? 'bg-slate-500'
              : ''} hover:bg-slate-300"
            on:click={() => goToItem(item)}
          >
            <div class={Object.values(item.views).length > 1 ? "grid grid-cols-2" : ""}>
              {#each Object.values(item.views) as itemView}
                <img
                  src={itemView.thumbnail}
                  alt="{item.id} - {itemView.id}"
                  class="w-24 h-24 p-1 object-cover rounded"
                />
              {/each}
            </div>
            <div class="flex mx-auto">
              <span
                class="text-xs justify-center truncate grow text-slate-100 {Object.values(
                  item.views,
                ).length > 1
                  ? 'w-48'
                  : 'w-24'}"
                title={item.id}
              >
                {item.id}
              </span>
            </div>
          </button>
        {/each}
      {/each}
    </div>
  </div>
</div>
