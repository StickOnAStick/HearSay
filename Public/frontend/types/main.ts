import PocketBase, {RecordModel} from 'pocketbase';
export default interface Review extends RecordModel {
    summary: string
    text: string
    helpfulnessdenominator: number
    helpfulnessnumerator: number
    id_: number // The original ID from Amazon Fine food Reviews
    profilename: string
    score: number
    time: number
    labels: string[]
}