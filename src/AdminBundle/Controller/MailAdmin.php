<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 03.08.18
 * Time: 12:50
 */

namespace AdminBundle\Controller;

use Sonata\AdminBundle\Admin\AbstractAdmin;
use Sonata\AdminBundle\Datagrid\DatagridMapper;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use ThoughtBundle\Entity\GeneralMail;

class MailAdmin extends AbstractAdmin
{
    private $rootPath;

    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('subject')
            ->add('body', 'textarea', [
                'label' => 'Message',
                'attr'  => [
                    'class' => 'js-ckeditor',
                ],
            ]);
    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
//            ->add('mailTo')
            ->addIdentifier('subject' ,null, [
                'header_style' => 'width: 15%',
            ])
            ->add('body', 'html', [
                'strip' => true
            ])
            ->add('isSended', null, [
                'header_style' => 'width: 10%; text-align: center;',
                'row_align' => 'center',
            ]);
    }

    /**
     * @param DatagridMapper $datagridMapper
     */
    protected function configureDatagridFilters(DatagridMapper $datagridMapper)
    {
        foreach ($this->getFilterFields() as $filterField) {
            $datagridMapper->add($filterField);
        }
    }

    /**
     * @return array
     */
    public function getFilterFields()
    {
        return [
            //            'mailTo',
            'subject',
            'body',
            'isSended',
        ];
    }

    public function setMyRootPath($rootPath)
    {
        $this->rootPath = $rootPath;
    }

    public function postPersist($object)
    {
        $this->sendEmailForAllUsers($object);
    }

    public function postUpdate($object)
    {
        $this->sendEmailForAllUsers($object);
    }

    private function sendEmailForAllUsers($object)
    {
        $root = $this->rootPath;
        /** @var GeneralMail $object */
        $mailId  = $object->getId();
        $command = 'nohup php "' . $root . '/console" throught:mail_command ' . $mailId . ' >> ' . $root . '/logs/mail_command_out.log 2>&1 &';


        exec($command);
    }

    public function toString($object)
    {
        return $object instanceof GeneralMail
            ? $object->getSubject()
            : 'Email';
    }
}