export const veryLongText = `Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris ac eleifend quam. Pellentesque et lectus ac ex porta molestie. Curabitur sed vestibulum turpis, id ullamcorper quam. Sed ut finibus sapien, et auctor ex. Vivamus tincidunt nisi nec est fermentum, sit amet gravida magna auctor. Aliquam erat volutpat. Nam nec dictum orci. Phasellus sed consequat enim. Integer sit amet ex ut arcu tempus euismod. Donec nec urna eu justo elementum semper. Fusce vitae consectetur augue, id aliquet eros. Praesent ac nibh vel erat lacinia consectetur vel eu nisi. Maecenas scelerisque, sapien at cursus molestie, nisl augue sodales nulla, eget scelerisque magna est sed dui.
Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Proin ut sem id urna convallis blandit. Donec efficitur sapien eu quam egestas, vel convallis odio consequat.
At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus.`;

type sampleMessagesType = {
    role: "user" | "bot",
    text: string
}

export const sampleMessages: sampleMessagesType[] = [
  {
    role: "user",
    text: "What is the meaning of Termination for convenience clause ?",
  },
  {
    role: "bot",
    text: "Commission may terminate this Agreement for its convenience any time, in whole or part, by giving consultant thirty-day (30-day) written notice",
  },
  {
    role: "user",
    text: "What is the requirement for Claims-made policy tail coverage ?"
  },
  {
    role: "bot",
    text: "If any insurance coverage required in the Agreement is provided on a 'Claims Made' rather than 'Occurrence' form, Consultant agrees to maintain the required coverage for a period of 3 years after the expiration of this Agreement and any extensions thereof."
  }
];

export const sampleSummary = `This Professional Services Agreement is between the Santa Cruz County Regional Transportation Commission (COMMISSION) and a Consultant. The COMMISSION can terminate for convenience with 30 days' notice or for cause with a 10-day cure period, while the CONSULTANT must give 120 days' notice.
The CONSULTANT's key duties include indemnifying the COMMISSION against claims arising from its negligence, maintaining specific insurance policies (like Professional Liability), and keeping all work confidential. The COMMISSION owns all deliverables. The CONSULTANT must also maintain records for five years for potential audits and follow all safety regulations.
Payments are made monthly up to a contractual limit, with the COMMISSION paying for work completed if it terminates for convenience. Disputes are resolved internally, and any changes to the agreement require a written amendment.`