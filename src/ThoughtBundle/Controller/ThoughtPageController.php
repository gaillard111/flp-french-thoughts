<?php

namespace ThoughtBundle\Controller;

use Application\Sonata\UserBundle\Entity\User;
use Exception;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use ThoughtBundle\Entity\Comment;
use ThoughtBundle\Entity\WatchedThought;
use ThoughtBundle\Form\CommentType;
use ThoughtBundle\Model\TopicChainModel;

/**
 * Class ThoughtPageController
 *
 * @package ThoughtBundle\Controller
 */
class ThoughtPageController extends Controller
{
    /**
     * @Route("/quote/{thoughtId}", requirements={"thoughtId"="\d+"})
     *
     * @param Request $request
     * @param int     $thoughtId
     *
     * @return RedirectResponse|Response
     *
     * @throws Exception
     */
    public function indexAction(Request $request, $thoughtId)
    {
        $em = $this->getDoctrine()->getManager();

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        $comment = new Comment();
        $comment->setThought($thought);

        $form = $this->createForm(new CommentType(), $comment);

        $role = User::ROLE_USER;

        if ($this->isGranted(User::ROLE_STUDENT)) {
            $role = User::ROLE_STUDENT;
        }

        if ($this->getUser()) {
            $watchedThought = $em->getRepository(WatchedThought::class)->findOneBy([
                'thought' => $thought,
            ]);

            if (!$watchedThought) {
                $watchedThought = new WatchedThought();
                $watchedThought
                    ->setThought($thought)
                    ->setUser($this->getUser());

                $em->persist($watchedThought);
                $em->flush();
            }

            $comment->setName($this->getUser()->getFirstName());
            $comment->setEmail($this->getUser()->getEmail());

            $form = $this->createForm(new CommentType(), $comment);

            if ($request->getMethod() == 'POST') {
                $form->handleRequest($request);

                if ($form->isValid()) {
                    $em->persist($comment);
                    $em->flush();

                    $serviceMail = $this->container->get('thought.service.mail_service');

                    $serviceMail->mailAddNewComment($comment);

                    $this->addFlash('success', $this->get('translator')->trans('thought.comment.added'));

                    return $this->redirect($this->generateUrl('thought_thoughtpage_index', ['thoughtId' => $thoughtId]));
                } else {
                    $this->addFlash('success', $this->get('translator')->trans('thought.comment.not_add'));
                }
            }
        }

        if (!$thought) {
            $this->addFlash('success', $this->get('translator')->trans('thought.not_found'));

            return $this->redirect($this->generateUrl('thought_homepage_index'));
        }

        $userIsStudent  = $this->isGranted(User::ROLE_STUDENT);

        if (is_null($thought->getOwner())) {
            $ownerIsStudent = false;
        } else {
            $ownerIsStudent = in_array(User::ROLE_STUDENT, $thought->getOwner()->getRoles());
        }

        if ($userIsStudent != $ownerIsStudent && (!$userIsStudent && $ownerIsStudent)) {
            $this->addFlash('success', $this->get('translator')->trans('thought.not_found'));

            return $this->redirect($this->generateUrl('thought_homepage_index'));
        }

        $comments[$thought->getId()][] = $em->getRepository(Comment::class)->getLastComments($thought);

        $collectiveChains = $em->getRepository('ThoughtBundle:Chain')->getAllCollectiveChains($role);


        /** @var TopicChainModel $modelTopicChain */
        $modelTopicChain = $this->container->get("thought.model.topicchain_model");

        // Get topics with chains for selector
            $topicsArray = $modelTopicChain->getTopicsWithChains();

            $topicPrivateItem = [];
            if ($this->getUser()) {
                $topicPrivateItem = $modelTopicChain->getUserPrivateChaines($this->getUser());
            }

            $topicsArray[] = $topicPrivateItem;
        //---

        // Array friends for related quotes
        $userFriend = [];
        $user = $this->getUser();
        if ($user) {
            foreach ($user->getFriends() as $friend) {
                $userFriend[$friend->getUser()->getId()] = $friend->getUser()->getFirstname();
            }
            $userFriend[$user->getId()] = 'Yours';
        }
        //---

        return $this->render('@Thought/thoughtPage.html.twig', [
            'thought'   => $thought,
            'comments'  => $comments,
            'form'      => $form->createView(),
            'colChains' => $collectiveChains->getResult(),
            'topicsArray' => $topicsArray,
            'userFriends' => $userFriend
        ]);
    }

    /**
     * @Route("/comment/{commentId}/remove", methods={"GET"}, requirements={"commentId"="\d+"})
     *
     * @param Request $request
     * @param int     $commentId
     *
     * @return RedirectResponse
     */
    public function deleteCommentAction(Request $request, $commentId)
    {
        $em = $this->getDoctrine()->getManager();

        $comment = $em->getRepository('ThoughtBundle:Comment')->find($commentId);

        if (!$comment) {
            $this->addFlash('success', $this->get('translator')->trans('thought.comment.not_found'));

            return $this->redirect($this->generateUrl('thought_homepage_index'));
        }

        try {
            $em->remove($comment);
            $em->flush();

            $this->addFlash('success', $this->get('translator')->trans('thought.comment.deleted'));
        } catch (Exception $e) {
            $this->addFlash('success', $e->getMessage());
        }

        return $this->redirect($this->generateUrl('thought_thoughtpage_index', ['thoughtId' => $comment->getThought()->getId()]));
    }
}
