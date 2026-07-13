export const htmlTemplates = {
    board: 1,
    status: 2,
    card: 3,
    addStatus: 4,
};

export const builderFunctions = {
    [htmlTemplates.board]: boardBuilder,
    [htmlTemplates.status]: statusBuilder,
    [htmlTemplates.card]: cardBuilder,
    [htmlTemplates.addStatus]: addStatusBuilder,
};

export function htmlFactory(template) {
    if (builderFunctions.hasOwnProperty(template)) {
        return builderFunctions[template];
    }

    console.error("Undefined template: " + template);

    return () => {
        return "";
    };
}

function addStatusBuilder(boardId) {
    return `<div class="col-12 col-sm-6 col-md-4 col-lg-3 board__status-column flex-column">
                <h4 class="board__status-header mb-0 d-flex align-items-center justify-content-center">
                    <input
                        class="board__status-input board__status-input--new"
                        placeholder="New Column"
                        data-board-id='${boardId}'
                    />
                </h4>
            </div>`;
}

function boardBuilder(board) {
    return `<div class="accordion-item board">
    <h2 class="accordion-header position-relative" id="heading${board.id}">
        <input class="board__title-input" data-board-id="${board.id}"
            data-board-private="${board.is_private}" value="${board.title}">
        <button class="btn board__add-card-button" data-board-id="${board.id}">+ Add card</button>
        <button class="btn btn-sm button-delete delete-board" data-board-id="${board.id}"><i class="fa-solid fa-trash-can"></i></button>
        <div class="accordion-button align-items-baseline collapsed" type="button" data-bs-toggle="collapse"
            data-bs-target="#collapse${board.id}" aria-expanded="false" aria-controls="collapse${board.id}" data-board-id="${board.id}">
        </div>
    </h2>
    <div id="collapse${board.id}" class="accordion-collapse collapse" aria-labelledby="heading${board.id}"
        data-bs-parent="#accordionBoards">
        <div class="accordion-body">
            <div class="row board__body status-droppable" data-board-id="${board.id}">
            </div>
        </div>
    </div>
</div>`;
}

function statusBuilder(status) {
    return `<div class="col-12 col-sm-6 col-md-4 col-lg-3 col-xxl-2 board__status-column flex-column status-draggable" data-status-id="${status.id}" data-status-order="${status.status_order}" data-board-id="${status.board_id}" draggable="true">
                <h4 class="board__status-header mb-0 d-flex align-items-center pt-1">
                    <input class="board__status-input" value="${status.title}" data-status-id="${status.id}" data-board-id="${status.board_id}"/>
                    <button class="btn btn-sm button-delete delete-status" data-board-id="${status.board_id}" data-status-id="${status.id}"><i class="fa-solid fa-trash-can"></i></button>
                </h4>
                <div class="board__card-container container d-flex flex-column card-droppable" data-board-id="${status.board_id}" data-status-id="${status.id}">
                </div>
            </div>`;
}

function cardBuilder(card) {
    return `<fieldset class="card card-draggable" data-card-id="${card.id}" data-card-order="${card.card_order}" data-board-id="${card.board_id}" data-card-archived="${card.archived}" data-status-id="${card.status_id}" draggable="true">
                <div class="card-body">
                    <h5 class="card-title">
                        <input type="text" class="board__card-title" value="${card.title}" data-card-id="${card.id}" data-board-id="${card.board_id}" data-status-id="${card.status_id}" data-card-order="${card.order}" data-card-archived="${card.archived}"/>
                        <button class="btn btn-sm button-delete delete-card" data-board-id="${card.board_id}" data-card-id="${card.id}"><i class="fa-solid fa-trash-can"></i></button>
                    </h5>
                    <textarea class="card-text board__card-text" placeholder="Card description" data-card-id="${card.id}" data-board-id="${card.board_id}">${card.body}</textarea>
                </div>
            </fieldset>`;
}
