import { dataHandler } from "../data/dataHandler.js";

export const TYPES = {
  BOARD: "board",
  STATUS_DRAG: "statusDrag",
  STATUS_DROP: "statusDrop",
  CARD: "card",
};

export let dragManager = {
  initDragElements: function () {
    document.querySelectorAll("fieldset.card-draggable").forEach((card) => {
      dragManager.handleNewElement(card, TYPES.CARD);
    });
    document.querySelectorAll(".status-draggable").forEach((status) => {
      dragManager.handleNewElement(status, TYPES.STATUS_DRAG);
    });
    document.querySelectorAll(".card-droppable").forEach((status) => {
      dragManager.handleNewElement(status, TYPES.STATUS_DROP);
    });
    document.querySelectorAll(".status-droppable").forEach((board) => {
      dragManager.handleNewElement(board, TYPES.BOARD);
    });
  },
  handleNewElement: function (elem, type) {
    switch (type) {
      case TYPES.BOARD:
        elem.addEventListener("dragover", statusDragOver);
        break;
      case TYPES.STATUS_DRAG:
        elem.addEventListener("dragstart", statusDragStart);
        elem.addEventListener("dragend", statusDragEnd);
        break;
      case TYPES.STATUS_DROP:
        elem.addEventListener("dragover", cardDragOver);
        break;
      case TYPES.CARD:
        elem.addEventListener("dragstart", cardDragStart);
        elem.addEventListener("dragend", cardDragEnd);
        break;
    }
  },

};

function cardDragStart(event) {
  event.stopPropagation();
  this.classList.add("card-dragging");
}

async function cardDragEnd(event) {
  event.stopPropagation();
  this.classList.remove("card-dragging");
  await fixCardOrder(this);
}

function statusDragStart(event) {
  event.stopPropagation();
  this.classList.add("status-dragging");
}

async function statusDragEnd(event) {
  event.stopPropagation();
  this.classList.remove("status-dragging");
  await fixStatusOrder(this);
}

let isStatusThrottled = false;

function statusDragOver(event) {
  event.preventDefault();
  
  if (isStatusThrottled) return;
  isStatusThrottled = true;

  const currentTarget = event.currentTarget;
  const clientX = event.clientX;

  requestAnimationFrame(() => {
    try {
      const draggable = document.querySelector(".status-dragging");

      if (
        draggable &&
        currentTarget.classList.contains("status-droppable") &&
        draggable.dataset.boardId === currentTarget.dataset.boardId
      ) {
        const nextSibling = getDragNextStatusSibling(
          currentTarget,
          clientX,
        );
        const addColumnButton = currentTarget.querySelector(
          ".board__status-column:not(.status-draggable)",
        );

        currentTarget.insertBefore(draggable, nextSibling || addColumnButton);
      }
    } finally {
      isStatusThrottled = false;
    }
  });
}

let isCardThrottled = false;

function cardDragOver(event) {
  event.preventDefault();
  
  if (isCardThrottled) return;
  isCardThrottled = true;

  const currentTarget = event.currentTarget;
  const clientY = event.clientY;

  requestAnimationFrame(() => {
    try {
      const draggable = document.querySelector(".card-dragging");

      if (
        draggable &&
        currentTarget.classList.contains("card-droppable") &&
        draggable.dataset.boardId === currentTarget.dataset.boardId
      ) {
        const nextSibling = getDragNextCardSibling(
          currentTarget,
          clientY,
        );
        if (!nextSibling) {
          currentTarget.appendChild(draggable);
        } else {
          currentTarget.insertBefore(draggable, nextSibling);
        }
      }
    } finally {
      isCardThrottled = false;
    }
  });
}
function getDragNextSibling(container, coordinate, axis, selector) {
  const draggableElements = container.querySelectorAll(selector);
  let closest = { offset: Number.NEGATIVE_INFINITY, element: null };

  for (const child of draggableElements) {
    const box = child.getBoundingClientRect();
    const offset =
      coordinate -
      (axis === "y" ? box.top : box.left) -
      (axis === "y" ? box.height : box.width) / 2;
      
    if (offset < 0 && offset > closest.offset) {
      closest = { offset: offset, element: child };
    }
  }
  
  return closest.element;
}

function getDragNextCardSibling(container, y) {
  return getDragNextSibling(
    container,
    y,
    "y",
    ".card-draggable:not(.card-dragging)",
  );
}

function getDragNextStatusSibling(container, x) {
  return getDragNextSibling(
    container,
    x,
    "x",
    ".status-draggable:not(.status-dragging)",
  );
}

async function fixStatusOrder(element) {
  const allSiblings = [...element.parentElement.children];
  let i = 1;
  const updatePromises = [];

  for (let sibling of allSiblings) {
    if ("statusOrder" in sibling.dataset) {
      if (parseInt(sibling.dataset.statusOrder, 10) !== i) {
        let boardId = sibling.dataset.boardId;
        let statusId = sibling.dataset.statusId;
        sibling.dataset.statusOrder = `${i}`;
        updatePromises.push(
          dataHandler.updateStatus(boardId, statusId, {
            status_order: i,
          }),
        );
      }
      i += 1;
    }
  }

  try {
    await Promise.all(updatePromises);
  } catch (error) {
    console.error("Błąd aktualizacji kolejności statusów:", error);
    alert("Nie udało się zapisać zmian w statusach. Odśwież stronę.");
  }
}

async function fixCardOrder(element) {
  const allSiblings = [...element.parentElement.children];
  let i = 1;
  const updatePromises = [];

  for (let sibling of allSiblings) {
    if ("cardOrder" in sibling.dataset) {
      let boardId = sibling.dataset.boardId;
      let newColumnStatusId = element.parentElement.dataset.statusId;
      let cardId = sibling.dataset.cardId;

      const statusChanged = sibling.dataset.statusId !== newColumnStatusId;
      const orderChanged = parseInt(sibling.dataset.cardOrder, 10) !== i;

      if (statusChanged || orderChanged) {
        sibling.dataset.cardOrder = `${i}`;
        sibling.dataset.statusId = newColumnStatusId;
        updatePromises.push(
          dataHandler.updateCard(boardId, cardId, {
            status_id: newColumnStatusId,
            card_order: i,
          }),
        );
      }
      i += 1;
    }
  }

  try {
    await Promise.all(updatePromises);
  } catch (error) {
    console.error("Błąd aktualizacji kolejności kart:", error);
    alert("Nie udało się zapisać zmian w kartach. Odśwież stronę.");
  }
}
