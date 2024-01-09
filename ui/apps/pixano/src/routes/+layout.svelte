<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";

  import type { DatasetInfo } from "@pixano/core/src";
  import { api } from "@pixano/core/src";

  import MainHeader from "../components/layout/MainHeader.svelte";
  import DatasetHeader from "../components/layout/DatasetHeader.svelte";
  import { datasetsStore, modelsStore, datasetTableStore } from "../lib/stores/datasetStores";

  import "./styles.css";

  let datasets: DatasetInfo[] = [];
  let models: Array<string>;
  let pageId: string | null;
  let currentDatasetName: string;

  async function handleGetModels() {
    console.log("App.handleGetModels");

    models = await api.getModels();
    modelsStore.set(models);
  }

  async function handleGetDatasets() {
    const loadedDatasets = await api.getDatasets();
    datasets = loadedDatasets ? loadedDatasets : [];

    if (loadedDatasets?.length > 0) {
      datasetsStore.set(loadedDatasets);
    }
  }

  onMount(async () => {
    await handleGetDatasets();
    await handleGetModels();
  });

  const getDatasetItems = async (datasetId: string, page?: number, size?: number) => {
    const datasetItems = await api.getDatasetItems(datasetId, page, size);
    datasetsStore.update((value = []) =>
      value.map((dataset) =>
        dataset.id === datasetId ? { ...dataset, page: datasetItems } : dataset,
      ),
    );
  };

  $: page.subscribe((value) => {
    pageId = value.route.id;
    currentDatasetName = value.params.dataset;
  });

  $: {
    const currentDatasetId = datasets?.find((dataset) => dataset.name === currentDatasetName)?.id;
    if (currentDatasetId) {
      //TODO make page param more robust according to page min/max etc... (can be edited by user!)
      let datasetPage = undefined;
      const queryParam = $page.url.searchParams.get("page");
      if(queryParam) {
        datasetPage = Number(queryParam);
        if (isNaN(datasetPage)) datasetPage = undefined;
      }
      console.log("qpage", $page.url.searchParams.get("page"), datasetPage);
      getDatasetItems(currentDatasetId, datasetPage).catch((err) =>
        console.error(err),
      );
    }
  }

  datasetTableStore.subscribe((value) => {
    const currentDatasetId = datasets?.find((dataset) => dataset.name === currentDatasetName)?.id;
    if (currentDatasetId && value) {
      console.log("HERETOO!!", pageId, value.currentPage);
      getDatasetItems(currentDatasetId, value.currentPage, value.pageSize).catch((err) =>
        console.error(err),
      );
      $page.url.searchParams.set("page", value.currentPage.toString());
      history.replaceState(history.state, "", $page.url);
    }
  });
</script>

<div class="app">
  {#if pageId === "/"}
    <MainHeader {datasets} />
  {:else}
    <DatasetHeader datasetName={currentDatasetName} {pageId} {currentDatasetName} />
  {/if}
  <main class="pt-20 h-1 min-h-screen">
    <slot />
  </main>
</div>
