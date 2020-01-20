<?php

namespace ThoughtBundle\Controller;

use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use ThoughtBundle\Entity\Comment;
use ThoughtBundle\Entity\WatchedThought;
use ThoughtBundle\Form\CommentType;

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
     * @return \Symfony\Component\HttpFoundation\RedirectResponse|\Symfony\Component\HttpFoundation\Response
     *
     * @throws \Exception
     */
    public function indexAction(Request $request, $thoughtId)
    {
        $em = $this->getDoctrine()->getManager();

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        $comment = new Comment();
        $comment->setThought($thought);

        $form = $this->createForm(new CommentType(), $comment);

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

        $comments[$thought->getId()][] = $em->getRepository(Comment::class)->getLastComments($thought);

        $collectiveChains = $em->getRepository('ThoughtBundle:Chain')->findBy([
            'isCollective' => true,
        ]);

        return $this->render('@Thought/thoughtPage.html.twig', [
            'thought'   => $thought,
            'comments'  => $comments,
            'form'      => $form->createView(),
            'colChains' => $collectiveChains,
        ]);
    }

    /**
     * @Route("/comment/{commentId}/remove", methods={"GET"}, requirements={"commentId"="\d+"})
     *
     * @param Request $request
     * @param int     $commentId
     *
     * @return \Symfony\Component\HttpFoundation\RedirectResponse
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
        } catch (\Exception $e) {
            $this->addFlash('success', $e->getMessage());
        }

        return $this->redirect($this->generateUrl('thought_thoughtpage_index', ['thoughtId' => $comment->getThought()->getId()]));
    }
}
