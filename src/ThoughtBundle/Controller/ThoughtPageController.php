<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use ThoughtBundle\Entity\Comment;
use ThoughtBundle\Entity\Thought;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use ThoughtBundle\Form\CommentType;

/**
 * Class ThoughtPageController
 * @package ThoughtBundle\Controller
 */
class ThoughtPageController extends Controller
{
    /**
     * @Route("/quote/{thoughtId}", requirements={"thoughtId"="\d+"})
     *
     * @param Request $request
     * @param int     $thoughtId
     * @return \Symfony\Component\HttpFoundation\RedirectResponse|\Symfony\Component\HttpFoundation\Response
     */
    public function indexAction(Request $request, $thoughtId)
    {
        $em = $this->getDoctrine()->getManager();

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        $comment = new Comment();
        $comment->setThought($thought);

        if ($this->getUser()) {
            $comment->setName($this->getUser()->getFirstName());
            $comment->setEmail($this->getUser()->getEmail());
        }

        $form = $this->createForm(new CommentType(), $comment);

        /*if ($request->getMethod() == 'POST') {
            $form->handleRequest($request);

            if ($form->isValid()) {
                $em->persist($comment);
                $em->flush();

                $serviceMail = $this->container->get('thought.service.mail_service');

                $serviceMail->mailAddNewComment($comment);

                $this->addFlash('success', $this->get('translator')->trans('thought.comment.added'));

                return $this->redirect($this->generateUrl('thought_thoughtpage_index', array('thoughtId' => $thoughtId)));
            } else {
                $this->addFlash('success', $this->get('translator')->trans('thought.comment.not_add'));
            }
        }*/

        if (!$thought) {
            $this->addFlash('success', $this->get('translator')->trans('thought.not_found'));

            return $this->redirect($this->generateUrl('thought_homepage_index'));
        }

        return $this->render('@Thought/thoughtPage.html.twig', array(
            'thought' => $thought,
            'form'    => $form->createView(),
        ));
    }

    /**
     * @Route("/comment/{commentId}/remove", methods={"GET"}, requirements={"commentId"="\d+"})
     *
     * @param Request $request
     * @param int     $commentId
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

        return $this->redirect($this->generateUrl('thought_thoughtpage_index', array('thoughtId' => $comment->getThought()->getId())));
    }
}
